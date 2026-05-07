"""Load business rules from YAML into PostgreSQL for downstream dbt models."""

import json

from app.utils.config import load_yaml
from app.utils.db import db_cursor
from app.utils.logging import get_logger


LOGGER = get_logger(__name__)


def load_business_rules() -> str:
    """Upsert the current business rule version into the raw rules table."""
    rules = load_yaml("app/config/business_rules.yaml")
    # The YAML file is the source of truth. We materialize it into PostgreSQL
    # so dbt can consume business parameters as a standard SQL relation.
    payload = {
        "rule_version": rules["rule_version"],
        "effective_from": rules["effective_from"],
        "office_address": rules["office_address"],
        "bonus_rate": rules["bonus_rate"],
        "wellbeing_days": rules["wellbeing_days"],
        "min_activities_per_year": rules["min_activities_per_year"],
        "max_km_walk_run": rules["max_km_walk_run"],
        "max_km_cycle_scooter_other": rules["max_km_cycle_scooter_other"],
        "sportive_transport_modes": json.dumps(rules["sportive_transport_modes"]),
    }

    with db_cursor() as (conn, cur):
        # The DDL is repeated here on purpose so the loader still works
        # against an already-running database whose init scripts were not replayed.
        cur.execute(
            """
            create table if not exists raw.business_rules_raw (
                rule_version text primary key,
                effective_from date not null,
                office_address text not null,
                bonus_rate numeric(8, 4) not null,
                wellbeing_days integer not null,
                min_activities_per_year integer not null,
                max_km_walk_run numeric(10, 2) not null,
                max_km_cycle_scooter_other numeric(10, 2) not null,
                sportive_transport_modes jsonb not null,
                loaded_at timestamptz not null default now()
            )
            """
        )
        cur.execute(
            """
            insert into raw.business_rules_raw (
                rule_version,
                effective_from,
                office_address,
                bonus_rate,
                wellbeing_days,
                min_activities_per_year,
                max_km_walk_run,
                max_km_cycle_scooter_other,
                sportive_transport_modes
            ) values (
                %(rule_version)s,
                %(effective_from)s,
                %(office_address)s,
                %(bonus_rate)s,
                %(wellbeing_days)s,
                %(min_activities_per_year)s,
                %(max_km_walk_run)s,
                %(max_km_cycle_scooter_other)s,
                %(sportive_transport_modes)s::jsonb
            )
            on conflict (rule_version) do update
            set
                effective_from = excluded.effective_from,
                office_address = excluded.office_address,
                bonus_rate = excluded.bonus_rate,
                wellbeing_days = excluded.wellbeing_days,
                min_activities_per_year = excluded.min_activities_per_year,
                max_km_walk_run = excluded.max_km_walk_run,
                max_km_cycle_scooter_other = excluded.max_km_cycle_scooter_other,
                sportive_transport_modes = excluded.sportive_transport_modes,
                loaded_at = now()
            """,
            payload,
        )
        conn.commit()

    LOGGER.info("Business rules loaded for version=%s", payload["rule_version"])
    return payload["rule_version"]


if __name__ == "__main__":
    load_business_rules()
