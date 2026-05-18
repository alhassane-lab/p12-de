"""Publish simulated sport activity events to the Redpanda topic."""

import argparse
import json
import os
from pathlib import Path

from confluent_kafka import Producer

from pipeline.simulation.generate_strava_like_activities import generate_activities_file
from pipeline.utils.config import ROOT_DIR
from pipeline.utils.logging import get_logger


LOGGER = get_logger(__name__)


def delivery_report(err, msg):
    """Log delivery failures when Kafka/Redpanda cannot persist a message."""
    if err is not None:
        LOGGER.error("Delivery failed for key=%s: %s", msg.key(), err)


def produce_activities(input_path: str | None = None) -> None:
    """Read the generated JSONL file and push each activity into Redpanda."""
    topic = os.getenv("REDPANDA_TOPIC", "sport_activities")
    brokers = os.getenv("REDPANDA_BROKERS", "localhost:19092")
    producer = Producer({"bootstrap.servers": brokers})

    source_path = Path(input_path) if input_path else Path(generate_activities_file(process_date=None))
    if not source_path.is_absolute():
        source_path = ROOT_DIR / source_path

    with source_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            producer.produce(
                topic=topic,
                key=payload["employee_id"],
                value=json.dumps(payload).encode("utf-8"),
                on_delivery=delivery_report,
            )
    producer.flush()
    LOGGER.info("Published activities from %s to %s", source_path, topic)


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI used to publish one daily activity batch."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-path", dest="input_path", help="Optional JSONL file to publish.")
    parser.add_argument("--process-date", dest="process_date", help="Logical processing date in YYYY-MM-DD format.")
    return parser


def produce_activities_for_date(input_path: str | None = None, process_date: str | None = None) -> None:
    """Publish a specific daily batch, generating it first when no file is provided."""
    resolved_input = input_path or generate_activities_file(process_date=process_date)
    produce_activities(input_path=resolved_input)


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    produce_activities_for_date(input_path=args.input_path, process_date=args.process_date)
