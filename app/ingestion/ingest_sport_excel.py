"""Ingest the declarative sport Excel workbook into the raw landing table."""

from pathlib import Path

from app.ingestion.common import build_row_hash, insert_dataframe, read_excel
from app.utils.logging import get_logger


LOGGER = get_logger(__name__)


SOURCE_PATH = "data/raw/Données+Sportive.xlsx"
INSERT_SQL = """
    insert into raw.sport_declarations_raw (
        ingestion_id, source_file, employee_id, declared_sport, row_hash
    )
    values (
        %(ingestion_id)s, %(source_file)s, %(employee_id)s, %(declared_sport)s, %(row_hash)s
    )
"""


def map_row(record: dict, ingestion_id: str) -> dict:
    """Map one sport declaration row to the raw table payload."""
    payload = {
        "ingestion_id": ingestion_id,
        "source_file": Path(SOURCE_PATH).name,
        "employee_id": str(record.get("ID salarié", "")).replace(".0", ""),
        "declared_sport": record.get("Pratique d'un sport"),
    }
    payload["row_hash"] = build_row_hash(payload)
    return payload


def ingest_sport_excel() -> str:
    """Load the sport declaration Excel source into PostgreSQL."""
    df = read_excel(SOURCE_PATH)
    LOGGER.info("Loaded %s sport declaration rows from Excel", len(df))
    return insert_dataframe(df, INSERT_SQL, map_row)


if __name__ == "__main__":
    ingest_sport_excel()
