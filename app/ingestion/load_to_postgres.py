"""Entry point used to load all static Excel sources into PostgreSQL."""

from app.ingestion.ingest_rh_excel import ingest_rh_excel
from app.ingestion.ingest_sport_excel import ingest_sport_excel


def load_static_sources() -> None:
    """Execute the static ingestion sequence for RH and sport declarations."""
    ingest_rh_excel()
    ingest_sport_excel()


if __name__ == "__main__":
    load_static_sources()
