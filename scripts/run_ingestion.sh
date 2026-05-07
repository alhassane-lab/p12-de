#!/usr/bin/env bash
set -euo pipefail

python -m app.config.load_business_rules
python -m app.ingestion.load_to_postgres
python -m app.simulation.generate_strava_like_activities
