"""Generate a deterministic JSONL file of Strava-like sport activities."""

import argparse
import hashlib
import json
import random
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

from pipeline.utils.config import ROOT_DIR, load_yaml
from pipeline.utils.db import db_cursor
from pipeline.utils.logging import get_logger


LOGGER = get_logger(__name__)
SETTINGS = load_yaml("src/pipeline/config/settings.yaml")


SPORTS = [
    ("run", 4, 18, 30, 110),
    ("ride", 8, 45, 35, 140),
    ("walk", 2, 12, 20, 80),
    ("hike", 6, 20, 45, 100),
    ("swim", 1, 4, 25, 70),
]


def parse_process_date(process_date: str | None) -> date:
    """Parse the target processing date or fall back to today's UTC date."""
    if process_date:
        return datetime.strptime(process_date, "%Y-%m-%d").date()
    return datetime.now(UTC).date()


def output_path_for_date(target_date: date) -> Path:
    """Build the JSONL output file path for one process date."""
    return ROOT_DIR / f"data/generated/activities_{target_date.isoformat()}.jsonl"


def fetch_employee_ids() -> list[str]:
    """Fetch the list of employees that will receive simulated activities."""
    with db_cursor() as (_, cur):
        cur.execute("select distinct employee_id from raw.rh_employees_raw where employee_id is not null order by employee_id")
        rows = cur.fetchall()
    return [row["employee_id"] for row in rows]


def weighted_profile_for_employee(employee_id: str) -> str:
    """Assign one stable activity profile to each employee from weighted settings."""
    profiles = SETTINGS["simulation"]["employee_profiles"]
    ordered_profiles = list(profiles.items())
    total_weight = sum(profile["weight"] for _, profile in ordered_profiles)
    marker = (int(hashlib.md5(employee_id.encode("utf-8")).hexdigest()[:8], 16) % 10_000) / 10_000
    cumulative = 0.0
    for profile_name, profile in ordered_profiles:
        cumulative += profile["weight"] / total_weight
        if marker <= cumulative:
            return profile_name
    return ordered_profiles[-1][0]


def activities_count_for_day(employee_id: str, target_date: date, seed: int) -> int:
    """Generate the number of activities for one employee on one logical day."""
    profile_name = weighted_profile_for_employee(employee_id)
    profile = SETTINGS["simulation"]["employee_profiles"][profile_name]
    rng = random.Random(f"{seed}-{target_date.isoformat()}-{employee_id}-count")
    if rng.random() > profile["active_day_probability"]:
        return 0
    return rng.randint(
        profile["min_activities_per_active_day"],
        profile["max_activities_per_active_day"],
    )


def build_activity(employee_id: str, activity_date: datetime, seed: int) -> dict:
    """Create one simulated activity event for a given employee and date."""
    rng = random.Random(f"{seed}-{employee_id}-{activity_date.isoformat()}")
    activity_type, min_km, max_km, min_duration, max_duration = rng.choice(SPORTS)
    distance_km = round(rng.uniform(min_km, max_km), 2)
    duration_min = rng.randint(min_duration, max_duration + int(distance_km * 3))
    simulation_settings = SETTINGS["simulation"]

    # Invalid events are intentionally injected in small proportion so the quality
    # dashboard has visible anomalies without breaking the strict dbt distance test.
    if rng.random() < simulation_settings["invalid_activity_rate"]:
        duration_min = 0

    return {
        "activity_id": str(uuid.uuid4()),
        "employee_id": employee_id,
        "activity_type": activity_type,
        "activity_date": activity_date.date().isoformat(),
        "distance_km": distance_km,
        "duration_min": duration_min,
        "calories_burned": rng.randint(150, 950),
        "source_system": "strava_simulator",
        "event_ts": activity_date.replace(tzinfo=UTC).isoformat(),
        "process_date": activity_date.date().isoformat(),
    }


def generate_activities_file(process_date: str | None = None, seed: int = 42) -> str:
    """Generate the daily activity batch file used by the Redpanda producer."""
    target_date = parse_process_date(process_date)
    output_path = output_path_for_date(target_date)
    employee_ids = fetch_employee_ids()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with output_path.open("w", encoding="utf-8") as handle:
        for employee_id in employee_ids:
            # Each employee has a stable activity profile so backfills stay reproducible
            # while the dashboard still shows a mix of dormant, occasional and intense users.
            total_activities = activities_count_for_day(employee_id, target_date, seed)
            for _ in range(total_activities):
                time_rng = random.Random(f"{seed}-{target_date.isoformat()}-{employee_id}-{total}-time")
                activity_datetime = datetime.combine(
                    target_date,
                    datetime.min.time(),
                    tzinfo=UTC,
                ).replace(
                    hour=time_rng.randint(6, 21),
                    minute=time_rng.randint(0, 59),
                )
                activity = build_activity(employee_id, activity_datetime, seed)
                handle.write(json.dumps(activity, ensure_ascii=True) + "\n")
                total += 1
    LOGGER.info("Generated %s activities for process_date=%s in %s", total, target_date, output_path)
    return str(output_path)


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI used by local runs and Airflow tasks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--process-date", dest="process_date", help="Logical processing date in YYYY-MM-DD format.")
    parser.add_argument("--seed", type=int, default=42, help="Base seed used to keep the simulation reproducible.")
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    generate_activities_file(process_date=args.process_date, seed=args.seed)
