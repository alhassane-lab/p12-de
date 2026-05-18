"""Ingest the declarative sport Excel workbook into the raw landing table."""

import argparse
from pathlib import Path

from pipeline.ingestion.common import build_row_hash, insert_dataframe, read_excel, resolve_process_date
from pipeline.utils.db import db_cursor
from pipeline.utils.logging import get_logger


LOGGER = get_logger(__name__)


SOURCE_PATH = "data/raw/Données+Sportive.xlsx"
INSERT_SQL = """
    insert into raw.sport_declarations_raw (
        ingestion_id, process_date, source_file, employee_id, declared_sport, row_hash
    )
    values (
        %(ingestion_id)s, %(process_date)s, %(source_file)s, %(employee_id)s, %(declared_sport)s, %(row_hash)s
    )
"""


def ensure_table_shape() -> None:
    """Add process_date to the raw table when working on an already initialized database."""
    with db_cursor() as (conn, cur):
        cur.execute("alter table raw.sport_declarations_raw add column if not exists process_date date")
        conn.commit()


def purge_batch(process_date: str) -> None:
    """Delete the current logical batch so a replay stays idempotent for that day."""
    with db_cursor() as (conn, cur):
        cur.execute(
            "delete from raw.sport_declarations_raw where source_file = %s and process_date = %s",
            (Path(SOURCE_PATH).name, process_date),
        )
        conn.commit()


def map_row(record: dict, ingestion_id: str, process_date: str) -> dict:
    """Map one sport declaration row to the raw table payload."""
    payload = {
        "ingestion_id": ingestion_id,
        "process_date": process_date,
        "source_file": Path(SOURCE_PATH).name,
        "employee_id": str(record.get("ID salarié", "")).replace(".0", ""),
        "declared_sport": record.get("Pratique d'un sport"),
    }
    payload["row_hash"] = build_row_hash(payload)
    return payload


def ingest_sport_excel(process_date: str | None = None) -> str:
    """Load the sport declaration Excel source into PostgreSQL."""
    resolved_process_date = resolve_process_date(process_date)
    ensure_table_shape()
    purge_batch(resolved_process_date)
    df = read_excel(SOURCE_PATH)
    LOGGER.info("Loaded %s sport declaration rows from Excel", len(df))
    return insert_dataframe(df, INSERT_SQL, lambda record, ingestion_id: map_row(record, ingestion_id, resolved_process_date))


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI used by manual runs and Airflow tasks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--process-date", dest="process_date", help="Logical processing date in YYYY-MM-DD format.")
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    ingest_sport_excel(process_date=args.process_date)
