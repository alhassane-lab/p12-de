#!/usr/bin/env bash
set -euo pipefail

python -m app.config.load_business_rules
dbt deps
dbt run
dbt test
