"""Entry point used to load all static Excel sources into PostgreSQL."""

import argparse

from pipeline.ingestion.ingest_rh_excel import ingest_rh_excel
from pipeline.ingestion.ingest_sport_excel import ingest_sport_excel


def load_static_sources(process_date: str | None = None) -> None:
    """Execute the static ingestion sequence for RH and sport declarations."""
    ingest_rh_excel(process_date=process_date)
    ingest_sport_excel(process_date=process_date)


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI used by manual runs and Airflow tasks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--process-date", dest="process_date", help="Logical processing date in YYYY-MM-DD format.")
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    load_static_sources(process_date=args.process_date)
