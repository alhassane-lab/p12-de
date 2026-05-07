"""Consume Redpanda events into PostgreSQL and generate Slack payloads."""

import json
import os

from confluent_kafka import Consumer

from app.streaming.slack_message_simulator import persist_slack_message
from app.utils.db import db_cursor
from app.utils.logging import get_logger


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
        "topic": message.topic(),
        "partition_id": message.partition(),
        "offset_id": message.offset(),
        "event_ts": payload["event_ts"],
        "payload_json": json.dumps(payload),
    }
    with db_cursor() as (conn, cur):
        cur.execute(
            """
            insert into raw.sport_activities_stream_raw (
                event_id, topic, partition_id, offset_id, event_ts, payload_json
            ) values (
                %(event_id)s, %(topic)s, %(partition_id)s, %(offset_id)s, %(event_ts)s, %(payload_json)s::jsonb
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


def consume_activities(max_messages: int | None = None, idle_polls_limit: int = 5) -> int:
    """Consume activity events until the topic is idle or a limit is reached."""
    topic = os.getenv("REDPANDA_TOPIC", "sport_activities")
    consumer = build_consumer()
    consumer.subscribe([topic])
    count = 0
    idle_polls = 0

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
            count += 1
            LOGGER.info("Consumed activity %s for employee %s", payload["activity_id"], payload["employee_id"])
            if max_messages is not None and count >= max_messages:
                break
    finally:
        consumer.close()

    return count


if __name__ == "__main__":
    consume_activities()
