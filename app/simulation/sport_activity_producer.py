"""Publish simulated sport activity events to the Redpanda topic."""

import json
import os
from pathlib import Path

from confluent_kafka import Producer

from app.simulation.generate_strava_like_activities import generate_activities_file
from app.utils.config import ROOT_DIR
from app.utils.logging import get_logger


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

    source_path = Path(input_path) if input_path else Path(generate_activities_file())
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


if __name__ == "__main__":
    produce_activities()
