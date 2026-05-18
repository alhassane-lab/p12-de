"""Run a lightweight Great Expectations validation pass on curated project tables."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import great_expectations as gx
import pandas as pd

from pipeline.utils.config import ROOT_DIR
from pipeline.utils.db import db_cursor
from pipeline.utils.logging import get_logger


LOGGER = get_logger(__name__)
DEFAULT_REPORT_DIR = ROOT_DIR / "data/generated/great_expectations"


@dataclass(frozen=True)
class ValidationSpec:
    """Describe one SQL extract and the expectation suite applied to it."""

    name: str
    query: str
    suite: gx.ExpectationSuite


def fetch_dataframe(query: str) -> pd.DataFrame:
    """Load one validation dataset from PostgreSQL into memory."""
    with db_cursor() as (_, cur):
        cur.execute(query)
        rows = cur.fetchall()
        columns = [column.name for column in cur.description or []]
    return pd.DataFrame(rows, columns=columns)


def build_validation_specs() -> list[ValidationSpec]:
    """Assemble the expectation suites used by this project."""
    employees_suite = gx.ExpectationSuite(name="sil_employees_suite")
    employees_suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="employee_id"))
    employees_suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column="employee_id"))
    employees_suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(column="gross_salary", min_value=0, strict_min=True)
    )
    employees_suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(column="distance_km_to_office", min_value=0)
    )

    activities_suite = gx.ExpectationSuite(name="sil_sport_activities_suite")
    activities_suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="activity_id"))
    activities_suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column="activity_id"))
    activities_suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="employee_id"))
    activities_suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="activity_date"))
    activities_suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="distance_km", min_value=0))

    employee_status_suite = gx.ExpectationSuite(name="gold_kpi_employee_status_suite")
    employee_status_suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="employee_id"))
    employee_status_suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column="employee_id"))
    employee_status_suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(column="is_bonus_eligible", value_set=[True, False])
    )
    employee_status_suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(column="is_wellbeing_eligible", value_set=[True, False])
    )
    employee_status_suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(column="bonus_amount", min_value=0)
    )
    employee_status_suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(column="wellbeing_days_awarded", min_value=0)
    )

    return [
        ValidationSpec(
            name="sil_employees",
            query="""
                select employee_id, gross_salary, distance_km_to_office
                from public_silver.sil_employees
            """,
            suite=employees_suite,
        ),
        ValidationSpec(
            name="sil_sport_activities",
            query="""
                select activity_id, employee_id, activity_date, distance_km
                from public_silver.sil_sport_activities
            """,
            suite=activities_suite,
        ),
        ValidationSpec(
            name="gold_kpi_employee_status",
            query="""
                select
                    employee_id,
                    is_bonus_eligible,
                    is_wellbeing_eligible,
                    bonus_amount,
                    wellbeing_days_awarded
                from public_gold.gold_kpi_employee_status
            """,
            suite=employee_status_suite,
        ),
    ]


def run_validations(report_dir: Path) -> dict:
    """Execute all Great Expectations suites and return a JSON-serializable report."""
    context = gx.get_context(mode="ephemeral")
    datasource = context.data_sources.add_pandas(name="sport_data_runtime")

    validation_results: list[dict] = []
    overall_success = True

    for spec in build_validation_specs():
        dataframe = fetch_dataframe(spec.query)
        suite = context.suites.add_or_update(spec.suite)
        asset = datasource.add_dataframe_asset(name=spec.name)
        batch_definition = asset.add_batch_definition_whole_dataframe(name=f"{spec.name}_batch")
        validation = context.validation_definitions.add_or_update(
            gx.ValidationDefinition(
                name=f"{spec.name}_validation",
                data=batch_definition,
                suite=suite,
            )
        )
        result = validation.run(batch_parameters={"dataframe": dataframe})
        validation_payload = result.to_json_dict()
        validation_results.append(
            {
                "table": spec.name,
                "row_count": len(dataframe),
                "success": result.success,
                "statistics": validation_payload.get("statistics", {}),
                "details": validation_payload,
            }
        )
        overall_success = overall_success and result.success
        LOGGER.info(
            "Great Expectations validation on %s: success=%s checked_rows=%s",
            spec.name,
            result.success,
            len(dataframe),
        )

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "success": overall_success,
        "validations": validation_results,
    }

    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    latest_path = report_dir / "latest_validation_report.json"
    archived_path = report_dir / f"validation_report_{timestamp}.json"
    for target_path in (latest_path, archived_path):
        with target_path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=True, default=str)
    LOGGER.info("Great Expectations report written to %s and %s", latest_path, archived_path)
    return report


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the command line interface for local runs and Airflow."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-dir",
        default=str(DEFAULT_REPORT_DIR),
        help="Directory where JSON validation reports will be written.",
    )
    return parser


def main() -> None:
    """Run the configured suites and exit non-zero on failure."""
    args = build_arg_parser().parse_args()
    report = run_validations(Path(args.report_dir))
    if not report["success"]:
        raise SystemExit("Great Expectations validation failed. See the generated report for details.")


if __name__ == "__main__":
    main()
