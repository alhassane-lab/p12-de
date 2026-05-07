#!/usr/bin/env bash
set -euo pipefail

python -m app.config.load_business_rules
dbt run --full-refresh
dbt test
