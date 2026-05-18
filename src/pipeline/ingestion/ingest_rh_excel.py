"""Ingest the HR Excel workbook into the raw employee landing table."""

import argparse
from pathlib import Path

from pipeline.ingestion.common import build_row_hash, insert_dataframe, read_excel, resolve_process_date
from pipeline.utils.db import db_cursor
from pipeline.utils.logging import get_logger


LOGGER = get_logger(__name__)


SOURCE_PATH = "data/raw/Données+RH.xlsx"
INSERT_SQL = """
    insert into raw.rh_employees_raw (
        ingestion_id, process_date, source_file, employee_id, last_name, first_name, birth_date_raw,
        business_unit, hire_date_raw, gross_salary_raw, contract_type, cp_days_raw,
        home_address, declared_transport_mode, row_hash
    )
    values (
        %(ingestion_id)s, %(process_date)s, %(source_file)s, %(employee_id)s, %(last_name)s, %(first_name)s, %(birth_date_raw)s,
        %(business_unit)s, %(hire_date_raw)s, %(gross_salary_raw)s, %(contract_type)s, %(cp_days_raw)s,
        %(home_address)s, %(declared_transport_mode)s, %(row_hash)s
    )
"""


def ensure_table_shape() -> None:
    """Add process_date to the raw table when working on an already initialized database."""
    with db_cursor() as (conn, cur):
        cur.execute("alter table raw.rh_employees_raw add column if not exists process_date date")
        conn.commit()


def purge_batch(process_date: str) -> None:
    """Delete the current logical batch so a replay stays idempotent for that day."""
    with db_cursor() as (conn, cur):
        cur.execute(
            "delete from raw.rh_employees_raw where source_file = %s and process_date = %s",
            (Path(SOURCE_PATH).name, process_date),
        )
        conn.commit()


def map_row(record: dict, ingestion_id: str, process_date: str) -> dict:
    """Map one HR Excel row to the raw table payload."""
    payload = {
        "ingestion_id": ingestion_id,
        "process_date": process_date,
        "source_file": Path(SOURCE_PATH).name,
        "employee_id": str(record.get("ID salarié", "")).replace(".0", ""),
        "last_name": record.get("Nom"),
        "first_name": record.get("Prénom"),
        "birth_date_raw": str(record.get("Date de naissance", "")),
        "business_unit": record.get("BU"),
        "hire_date_raw": str(record.get("Date d'embauche", "")),
        "gross_salary_raw": str(record.get("Salaire brut", "")),
        "contract_type": record.get("Type de contrat"),
        "cp_days_raw": str(record.get("Nombre de jours de CP", "")),
        "home_address": record.get("Adresse du domicile"),
        "declared_transport_mode": record.get("Moyen de déplacement"),
    }
    payload["row_hash"] = build_row_hash(payload)
    return payload


def ingest_rh_excel(process_date: str | None = None) -> str:
    """Load the HR Excel source into PostgreSQL and return the ingestion id."""
    resolved_process_date = resolve_process_date(process_date)
    ensure_table_shape()
    purge_batch(resolved_process_date)
    df = read_excel(SOURCE_PATH)
    LOGGER.info("Loaded %s RH rows from Excel", len(df))
    return insert_dataframe(df, INSERT_SQL, lambda record, ingestion_id: map_row(record, ingestion_id, resolved_process_date))


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI used by manual runs and Airflow tasks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--process-date", dest="process_date", help="Logical processing date in YYYY-MM-DD format.")
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    ingest_rh_excel(process_date=args.process_date)
