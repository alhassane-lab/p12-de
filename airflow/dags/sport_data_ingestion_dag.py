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
DBT_DIR = f"{WORKSPACE}/dbt/sport_data_dbt"
COMMON_ENV = """
export PYTHONPATH=/opt/airflow/workspace
export POSTGRES_HOST=postgres
export POSTGRES_PORT=5432
export POSTGRES_DB=sport_data
export POSTGRES_USER=sport_user
export POSTGRES_PASSWORD=sport_pass
export REDPANDA_BROKERS=redpanda:9092
export REDPANDA_TOPIC=sport_activities
export SLACK_CHANNEL='#sport-avantages'
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
        )
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
        python -m app.config.load_business_rules
        """,
    )

    ingest_static_sources = BashOperator(
        task_id="ingest_static_sources",
        bash_command=f"""
        set -euo pipefail
        {COMMON_ENV}
        cd {WORKSPACE}
        python -m app.ingestion.load_to_postgres
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
        python -m app.simulation.generate_strava_like_activities
        """,
    )

    produce_events = BashOperator(
        task_id="produce_redpanda_events",
        bash_command=f"""
        set -euo pipefail
        {COMMON_ENV}
        cd {WORKSPACE}
        python -m app.simulation.sport_activity_producer
        """,
    )

    consume_events = BashOperator(
        task_id="consume_redpanda_events",
        bash_command=f"""
        set -euo pipefail
        {COMMON_ENV}
        cd {WORKSPACE}
        python -m app.streaming.redpanda_consumer
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
    generate_activities >> produce_events >> consume_events >> run_dbt >> test_dbt
