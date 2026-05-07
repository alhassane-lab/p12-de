#!/usr/bin/env bash
set -euo pipefail

python -m app.simulation.sport_activity_producer
python -m app.streaming.redpanda_consumer
