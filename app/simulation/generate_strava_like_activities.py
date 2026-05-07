"""Generate a deterministic JSONL file of Strava-like sport activities."""

import json
import random
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from faker import Faker

from app.utils.config import ROOT_DIR, load_yaml
from app.utils.db import db_cursor
from app.utils.logging import get_logger


LOGGER = get_logger(__name__)
FAKER = Faker("fr_FR")
SETTINGS = load_yaml("app/config/settings.yaml")
OUTPUT_PATH = ROOT_DIR / "data/generated/activities_12m.jsonl"


SPORTS = [
    ("run", 4, 18, 30, 110),
    ("ride", 8, 45, 35, 140),
    ("walk", 2, 12, 20, 80),
    ("hike", 6, 20, 45, 100),
    ("swim", 1, 4, 25, 70),
]


def fetch_employee_ids() -> list[str]:
    """Fetch the list of employees that will receive simulated activities."""
    with db_cursor() as (_, cur):
        cur.execute("select distinct employee_id from raw.rh_employees_raw where employee_id is not null order by employee_id")
        rows = cur.fetchall()
    return [row["employee_id"] for row in rows]


def build_activity(employee_id: str, activity_date: datetime) -> dict:
    """Create one simulated activity event for a given employee and date."""
    activity_type, min_km, max_km, min_duration, max_duration = random.choice(SPORTS)
    distance_km = round(random.uniform(min_km, max_km), 2)
    duration_min = random.randint(min_duration, max_duration + int(distance_km * 3))
    return {
        "activity_id": str(uuid.uuid4()),
        "employee_id": employee_id,
        "activity_type": activity_type,
        "activity_date": activity_date.date().isoformat(),
        "distance_km": distance_km,
        "duration_min": duration_min,
        "calories_burned": random.randint(150, 950),
        "source_system": "strava_simulator",
        "event_ts": activity_date.replace(tzinfo=UTC).isoformat(),
    }


def generate_activities_file(seed: int = 42) -> str:
    """Generate the demo activity history file used by the Redpanda producer."""
    # The fixed seed keeps the simulation reproducible for demos and replay scenarios.
    random.seed(seed)
    employee_ids = fetch_employee_ids()
    settings = SETTINGS["simulation"]
    months_history = settings["months_history"]
    start_date = datetime.now(UTC) - timedelta(days=30 * months_history)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        for employee_id in employee_ids:
            # We generate a variable number of activities per employee so the
            # wellbeing-days rule produces both eligible and non-eligible cases.
            total_activities = random.randint(
                settings["min_activities_per_employee"],
                settings["max_activities_per_employee"],
            )
            for _ in range(total_activities):
                random_day = start_date + timedelta(days=random.randint(0, months_history * 30))
                activity = build_activity(employee_id, random_day)
                handle.write(json.dumps(activity, ensure_ascii=True) + "\n")
                total += 1
    LOGGER.info("Generated %s activities in %s", total, OUTPUT_PATH)
    return str(OUTPUT_PATH)


if __name__ == "__main__":
    generate_activities_file()
