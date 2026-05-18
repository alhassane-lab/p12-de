"""Consume Redpanda events into PostgreSQL and generate Slack payloads."""

import argparse
import json
import os
from datetime import UTC, datetime

from confluent_kafka import Consumer

from pipeline.streaming.slack_message_simulator import persist_slack_message
from pipeline.utils.db import db_cursor
from pipeline.utils.logging import get_logger


LOGGER = get_logger(__name__)


def build_consumer() -> Consumer:
    """Create the Kafka-compatible consumer used against Redpanda."""
    brokers = os.getenv("REDPANDA_BROKERS", "localhost:19092")
    return Consumer(
        {
            "bootstrap.servers": brokers,
            "group.id": "sport-data-solution-consumer",
            "auto.offset.reset": "earliest",
        }
    )


def persist_event(message) -> dict:
    """Persist one consumed event and create the derived Slack message once."""
    payload = json.loads(message.value().decode("utf-8"))
    row = {
        "event_id": payload["activity_id"],
        "process_date": payload.get("process_date", payload["activity_date"]),
        "topic": message.topic(),
        "partition_id": message.partition(),
        "offset_id": message.offset(),
        "event_ts": payload["event_ts"],
        "payload_json": json.dumps(payload),
    }
    with db_cursor() as (conn, cur):
        cur.execute("alter table raw.sport_activities_stream_raw add column if not exists process_date date")
        cur.execute(
            """
            insert into raw.sport_activities_stream_raw (
                event_id, process_date, topic, partition_id, offset_id, event_ts, payload_json
            ) values (
                %(event_id)s, %(process_date)s, %(topic)s, %(partition_id)s, %(offset_id)s, %(event_ts)s, %(payload_json)s::jsonb
            )
            on conflict do nothing
            """,
            row,
        )
        inserted = cur.rowcount == 1
        conn.commit()
    # A replayed Redpanda message should not create a second Slack message
    # if the raw event already exists in bronze.
    if inserted:
        persist_slack_message(payload)
    else:
        LOGGER.info("Skipped duplicate event %s at offset %s", row["event_id"], row["offset_id"])
    return payload


def consume_activities(
    max_messages: int | None = None,
    idle_polls_limit: int = 5,
    process_date: str | None = None,
) -> int:
    """Consume activity events until the topic is idle or a limit is reached."""
    topic = os.getenv("REDPANDA_TOPIC", "sport_activities")
    consumer = build_consumer()
    consumer.subscribe([topic])
    count = 0
    idle_polls = 0
    target_process_date = process_date or datetime.now(UTC).date().isoformat()

    try:
        while True:
            message = consumer.poll(1.0)
            if message is None:
                idle_polls += 1
                if idle_polls >= idle_polls_limit:
                    break
                continue
            if message.error():
                LOGGER.error("Consumer error: %s", message.error())
                continue
            idle_polls = 0
            payload = persist_event(message)
            if payload.get("process_date") != target_process_date:
                LOGGER.warning(
                    "Consumed event %s with process_date=%s while current run expects %s",
                    payload["activity_id"],
                    payload.get("process_date"),
                    target_process_date,
                )
            count += 1
            LOGGER.info("Consumed activity %s for employee %s", payload["activity_id"], payload["employee_id"])
            if max_messages is not None and count >= max_messages:
                break
    finally:
        consumer.close()

    return count


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI used by manual runs and Airflow."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-messages", type=int, dest="max_messages", help="Optional maximum number of messages to consume.")
    parser.add_argument("--idle-polls-limit", type=int, default=5, dest="idle_polls_limit", help="Stop after this number of empty polls.")
    parser.add_argument("--process-date", dest="process_date", help="Logical processing date in YYYY-MM-DD format.")
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    consume_activities(
        max_messages=args.max_messages,
        idle_polls_limit=args.idle_polls_limit,
        process_date=args.process_date,
    )
