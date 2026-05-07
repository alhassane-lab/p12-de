"""Database connection helpers shared by Python ingestion and streaming jobs."""

import os
from contextlib import contextmanager

from psycopg import connect
from psycopg.rows import dict_row


def get_connection():
    """Create a PostgreSQL connection using environment-based configuration."""
    return connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "sport_data"),
        user=os.getenv("POSTGRES_USER", "sport_user"),
        password=os.getenv("POSTGRES_PASSWORD", "sport_pass"),
        row_factory=dict_row,
    )


@contextmanager
def db_cursor():
    """Yield a connection and cursor pair with automatic cleanup."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            yield conn, cur
