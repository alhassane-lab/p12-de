"""Load business rules from YAML into PostgreSQL for downstream dbt models."""

import json
from collections.abc import Mapping, Sequence

from pipeline.utils.config import load_yaml
from pipeline.utils.db import db_cursor
from pipeline.utils.logging import get_logger


LOGGER = get_logger(__name__)
RULES_YAML_PATH = "src/pipeline/config/business_rules.yaml"

# Legacy fields kept as first-class SQL columns because existing dbt models
# already depend on them directly. Any additional YAML keys are still loaded
# automatically through the generic JSON/key-value persistence below.
CORE_RULE_FIELDS = (
    "rule_version",
    "effective_from",
    "office_address",
    "bonus_rate",
    "wellbeing_days",
    "min_activities_per_year",
    "max_km_walk_run",
    "max_km_cycle_scooter_other",
)


def normalize_rules_payload(rules: Mapping) -> dict:
    """Convert YAML rules into a JSON-serializable payload."""
    normalized = dict(rules)
    sportive_transport_modes = normalized.get("sportive_transport_modes", [])
    normalized["sportive_transport_modes"] = list(sportive_transport_modes)
    return normalized


def flatten_rules(prefix: str, value) -> list[dict]:
    """Flatten nested YAML rules into key-value rows for generic persistence."""
    rows: list[dict] = []
    if isinstance(value, Mapping):
        for nested_key, nested_value in value.items():
            child_prefix = f"{prefix}.{nested_key}" if prefix else str(nested_key)
            rows.extend(flatten_rules(child_prefix, nested_value))
        return rows

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        rows.append(
            {
                "rule_path": prefix,
                "rule_value_json": json.dumps(value, ensure_ascii=True),
                "value_type": "array",
            }
        )
        return rows

    value_type = type(value).__name__
    rows.append(
        {
            "rule_path": prefix,
            "rule_value_json": json.dumps(value, ensure_ascii=True),
            "value_type": value_type,
        }
    )
    return rows


def build_legacy_payload(rules_payload: Mapping) -> dict:
    """Build the backward-compatible payload for the wide raw rules table."""
    missing = [field for field in CORE_RULE_FIELDS if field not in rules_payload]
    if missing:
        raise KeyError(f"Missing required business rule keys: {', '.join(missing)}")

    return {
        "rule_version": rules_payload["rule_version"],
        "effective_from": rules_payload["effective_from"],
        "office_address": rules_payload["office_address"],
        "bonus_rate": rules_payload["bonus_rate"],
        "wellbeing_days": rules_payload["wellbeing_days"],
        "min_activities_per_year": rules_payload["min_activities_per_year"],
        "max_km_walk_run": rules_payload["max_km_walk_run"],
        "max_km_cycle_scooter_other": rules_payload["max_km_cycle_scooter_other"],
        "sportive_transport_modes": json.dumps(rules_payload.get("sportive_transport_modes", [])),
        "rules_payload": json.dumps(rules_payload, ensure_ascii=True),
    }


def load_business_rules() -> str:
    """Upsert the current business rule version into the raw rules table."""
    rules = load_yaml(RULES_YAML_PATH)
    rules_payload = normalize_rules_payload(rules)
    payload = build_legacy_payload(rules_payload)
    flattened_rules = flatten_rules("", rules_payload)

    # The YAML file is the source of truth. We materialize it into PostgreSQL
    # so dbt can consume business parameters as a standard SQL relation.
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
                rules_payload jsonb not null default '{}'::jsonb,
                loaded_at timestamptz not null default now()
            )
            """
        )
        cur.execute(
            """
            alter table raw.business_rules_raw
            add column if not exists rules_payload jsonb not null default '{}'::jsonb
            """
        )
        cur.execute(
            """
            create table if not exists raw.business_rule_parameters_raw (
                rule_version text not null,
                rule_path text not null,
                rule_value_json jsonb not null,
                value_type text not null,
                loaded_at timestamptz not null default now(),
                primary key (rule_version, rule_path)
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
                sportive_transport_modes,
                rules_payload
            ) values (
                %(rule_version)s,
                %(effective_from)s,
                %(office_address)s,
                %(bonus_rate)s,
                %(wellbeing_days)s,
                %(min_activities_per_year)s,
                %(max_km_walk_run)s,
                %(max_km_cycle_scooter_other)s,
                %(sportive_transport_modes)s::jsonb,
                %(rules_payload)s::jsonb
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
                rules_payload = excluded.rules_payload,
                loaded_at = now()
            """,
            payload,
        )

        cur.execute(
            "delete from raw.business_rule_parameters_raw where rule_version = %(rule_version)s",
            {"rule_version": payload["rule_version"]},
        )
        cur.executemany(
            """
            insert into raw.business_rule_parameters_raw (
                rule_version,
                rule_path,
                rule_value_json,
                value_type
            ) values (
                %(rule_version)s,
                %(rule_path)s,
                %(rule_value_json)s::jsonb,
                %(value_type)s
            )
            """,
            [
                {
                    "rule_version": payload["rule_version"],
                    "rule_path": row["rule_path"],
                    "rule_value_json": row["rule_value_json"],
                    "value_type": row["value_type"],
                }
                for row in flattened_rules
            ],
        )
        conn.commit()

    LOGGER.info(
        "Business rules loaded for version=%s with %s flattened parameters from %s",
        payload["rule_version"],
        len(flattened_rules),
        RULES_YAML_PATH,
    )
    return payload["rule_version"]


if __name__ == "__main__":
    load_business_rules()
