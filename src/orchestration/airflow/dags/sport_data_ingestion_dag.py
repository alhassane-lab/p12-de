"""Airflow DAG orchestrating the full Sport Data Solution ingestion pipeline."""

from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.models.param import Param
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator
from airflow.utils.trigger_rule import TriggerRule


WORKSPACE = "/opt/airflow/workspace"
DBT_DIR = f"{WORKSPACE}/analytics/dbt"
COMMON_ENV = """
export PYTHONPATH=/opt/airflow/workspace/src
export POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export POSTGRES_DB="${POSTGRES_DB:-sport_data}"
export POSTGRES_USER="${POSTGRES_USER:?POSTGRES_USER is required}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
export REDPANDA_BROKERS="${REDPANDA_BROKERS:-redpanda:9092}"
export REDPANDA_TOPIC="${REDPANDA_TOPIC:-sport_activities}"
export SLACK_CHANNEL="${SLACK_CHANNEL:-#sport-avantages}"
"""


def resolved_process_date_expression() -> str:
    """Return the Airflow Jinja expression used to resolve the logical process date."""
    return "{{ params.process_date if params.process_date else ds }}"


def resolved_start_date_expression() -> str:
    """Resolve the first date of a possible backfill range."""
    return "{{ params.start_date or params.process_date or ds }}"


def resolved_end_date_expression() -> str:
    """Resolve the last date of a possible backfill range."""
    return "{{ params.end_date or params.process_date or ds }}"


def ranged_python_module_command(module_name: str) -> str:
    """Build a bash snippet that runs one module on each date of a backfill range."""
    return f"""
    export START_DATE="{resolved_start_date_expression()}"
    export END_DATE="{resolved_end_date_expression()}"
    python - <<'PY'
from datetime import datetime, timedelta
import os

start = datetime.strptime(os.environ["START_DATE"], "%Y-%m-%d").date()
end = datetime.strptime(os.environ["END_DATE"], "%Y-%m-%d").date()

if start > end:
    raise SystemExit(f"Invalid backfill range: {{start}} > {{end}}")

with open("/tmp/airflow_process_dates.txt", "w", encoding="utf-8") as handle:
    current = start
    while current <= end:
        handle.write(current.isoformat() + "\\n")
        current += timedelta(days=1)
PY

    while IFS= read -r process_date; do
        python -m {module_name} --process-date "$process_date"
    done < /tmp/airflow_process_dates.txt
    rm -f /tmp/airflow_process_dates.txt
    """


def choose_static_branch(**context) -> str:
    """Choose whether the DAG must replay the static ingestion branch."""
    # Airflow exposes DAG params to tasks. A manual trigger can override this
    # value, while scheduled runs keep the declared default below.
    run_static_load = context["params"].get("run_static_load", False)
    return "load_business_rules" if run_static_load else "skip_static_load"


with DAG(
    dag_id="sport_data_ingestion_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="0 8 * * *",
    catchup=False,
    tags=["sport-data", "poc", "ingestion"],
    default_args={"owner": "data-engineering"},
    params={
        "run_static_load": Param(
            default=False,
            type="boolean",
            title="Run static load",
            description="When true, replay business rules and Excel static sources before the daily flow.",
        ),
        "process_date": Param(
            default="",
            type=["null", "string"],
            title="Process date",
            description="Optional logical date in YYYY-MM-DD format. When empty, Airflow uses the run date.",
        ),
        "start_date": Param(
            default="",
            type=["null", "string"],
            title="Backfill start date",
            description="Optional first date of a backfill range in YYYY-MM-DD format.",
        ),
        "end_date": Param(
            default="",
            type=["null", "string"],
            title="Backfill end date",
            description="Optional last date of a backfill range in YYYY-MM-DD format.",
        ),
    },
) as dag:
    # This operator does not process data. It only chooses which branch to follow
    # by returning the task_id of the first task of the selected branch.
    branch_static_load = BranchPythonOperator(
        task_id="branch_static_load",
        python_callable=choose_static_branch,
    )

    # Empty task used as the "skip static load" branch.
    skip_static_load = EmptyOperator(task_id="skip_static_load")

    load_business_rules = BashOperator(
        task_id="load_business_rules",
        bash_command=f"""
        set -euo pipefail
        {COMMON_ENV}
        cd {WORKSPACE}
        python -m pipeline.config.load_business_rules
        """,
    )

    ingest_static_sources = BashOperator(
        task_id="ingest_static_sources",
        bash_command=f"""
        set -euo pipefail
        {COMMON_ENV}
        cd {WORKSPACE}
        {ranged_python_module_command("pipeline.ingestion.load_to_postgres")}
        """,
    )

    generate_activities = BashOperator(
        task_id="generate_activities",
        # This task is the merge point of two branches. One of them will always be
        # skipped, so the default all_success rule would incorrectly skip the rest
        # of the pipeline. We only require one successful upstream branch here.
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
        bash_command=f"""
        set -euo pipefail
        {COMMON_ENV}
        cd {WORKSPACE}
        {ranged_python_module_command("pipeline.simulation.generate_strava_like_activities")}
        """,
    )

    produce_events = BashOperator(
        task_id="produce_redpanda_events",
        bash_command=f"""
        set -euo pipefail
        {COMMON_ENV}
        cd {WORKSPACE}
        {ranged_python_module_command("pipeline.simulation.sport_activity_producer")}
        """,
    )

    consume_events = BashOperator(
        task_id="consume_redpanda_events",
        bash_command=f"""
        set -euo pipefail
        {COMMON_ENV}
        cd {WORKSPACE}
        python -m pipeline.streaming.redpanda_consumer
        """,
    )

    run_dbt = BashOperator(
        task_id="run_dbt",
        bash_command=f"""
        set -euo pipefail
        {COMMON_ENV}
        cd {DBT_DIR}
        cp -f profiles.yml.example profiles.yml
        dbt run
        """,
    )

    run_great_expectations = BashOperator(
        task_id="run_great_expectations",
        bash_command=f"""
        set -euo pipefail
        {COMMON_ENV}
        cd {WORKSPACE}
        python -m pipeline.data_quality.run_great_expectations
        """,
    )

    test_dbt = BashOperator(
        task_id="test_dbt",
        bash_command=f"""
        set -euo pipefail
        {COMMON_ENV}
        cd {DBT_DIR}
        cp -f profiles.yml.example profiles.yml
        dbt test
        """,
    )

    # These dependency lines define the two possible branches of the DAG:
    # 1. branch_static_load -> skip_static_load -> generate_activities
    # 2. branch_static_load -> load_business_rules -> ingest_static_sources -> generate_activities
    # The function choose_static_branch() decides which of these two paths Airflow keeps.
    branch_static_load >> skip_static_load >> generate_activities
    branch_static_load >> load_business_rules >> ingest_static_sources >> generate_activities

    # After the two branches merge on generate_activities, the rest of the pipeline
    # always runs in the same order.
    generate_activities >> produce_events >> consume_events >> run_dbt >> run_great_expectations >> test_dbt
