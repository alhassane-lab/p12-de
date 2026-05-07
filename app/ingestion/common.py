"""Shared helpers for Excel ingestion into PostgreSQL raw tables."""

import hashlib
import uuid
from pathlib import Path

import pandas as pd

from app.utils.db import db_cursor
from app.utils.logging import get_logger


LOGGER = get_logger(__name__)


ROOT_DIR = Path(__file__).resolve().parents[2]


def _row_hash(row: dict) -> str:
    """Build a deterministic hash used to track duplicate raw rows."""
    payload = "|".join("" if value is None else str(value) for value in row.values())
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_excel(path: str) -> pd.DataFrame:
    """Read an Excel source file from the repository root."""
    return pd.read_excel(ROOT_DIR / path)


def insert_dataframe(df: pd.DataFrame, insert_sql: str, row_mapper) -> str:
    """Insert a dataframe row by row after applying a source-specific mapper."""
    ingestion_id = str(uuid.uuid4())
    # A single ingestion_id lets us trace all rows loaded during one run.
    records = [row_mapper(record, ingestion_id) for record in df.to_dict(orient="records")]
    with db_cursor() as (conn, cur):
        cur.executemany(insert_sql, records)
        conn.commit()
    LOGGER.info("Inserted %s records with ingestion_id=%s", len(records), ingestion_id)
    return ingestion_id


def build_row_hash(record: dict) -> str:
    """Expose the internal hashing logic with a clearer public name."""
    return _row_hash(record)
