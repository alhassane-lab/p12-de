"""Convenience entry point to preload rules, raw sources and demo activities."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from pipeline.config.load_business_rules import load_business_rules
from pipeline.ingestion.ingest_rh_excel import ingest_rh_excel
from pipeline.ingestion.ingest_sport_excel import ingest_sport_excel
from pipeline.simulation.generate_strava_like_activities import generate_activities_file


if __name__ == "__main__":
    # This entry point is useful for a quick local bootstrap outside Airflow.
    load_business_rules()
    ingest_rh_excel()
    ingest_sport_excel()
    output_path = generate_activities_file()
    print(f"Initialisation terminee. Activites generees dans {output_path}")
