"""Ingest the HR Excel workbook into the raw employee landing table."""

from pathlib import Path

from app.ingestion.common import build_row_hash, insert_dataframe, read_excel
from app.utils.logging import get_logger


LOGGER = get_logger(__name__)


SOURCE_PATH = "data/raw/Données+RH.xlsx"
INSERT_SQL = """
    insert into raw.rh_employees_raw (
        ingestion_id, source_file, employee_id, last_name, first_name, birth_date_raw,
        business_unit, hire_date_raw, gross_salary_raw, contract_type, cp_days_raw,
        home_address, declared_transport_mode, row_hash
    )
    values (
        %(ingestion_id)s, %(source_file)s, %(employee_id)s, %(last_name)s, %(first_name)s, %(birth_date_raw)s,
        %(business_unit)s, %(hire_date_raw)s, %(gross_salary_raw)s, %(contract_type)s, %(cp_days_raw)s,
        %(home_address)s, %(declared_transport_mode)s, %(row_hash)s
    )
"""


def map_row(record: dict, ingestion_id: str) -> dict:
    """Map one HR Excel row to the raw table payload."""
    payload = {
        "ingestion_id": ingestion_id,
        "source_file": Path(SOURCE_PATH).name,
        "employee_id": str(record.get("ID salarié", "")).replace(".0", ""),
        "last_name": record.get("Nom"),
        "first_name": record.get("Prénom"),
        "birth_date_raw": str(record.get("Date de naissance", "")),
        "business_unit": record.get("BU"),
        "hire_date_raw": str(record.get("Date d'embauche", "")),
        "gross_salary_raw": str(record.get("Salaire brut", "")),
        "contract_type": record.get("Type de contrat"),
        "cp_days_raw": str(record.get("Nombre de jours de CP", "")),
        "home_address": record.get("Adresse du domicile"),
        "declared_transport_mode": record.get("Moyen de déplacement"),
    }
    payload["row_hash"] = build_row_hash(payload)
    return payload


def ingest_rh_excel() -> str:
    """Load the HR Excel source into PostgreSQL and return the ingestion id."""
    df = read_excel(SOURCE_PATH)
    LOGGER.info("Loaded %s RH rows from Excel", len(df))
    return insert_dataframe(df, INSERT_SQL, map_row)


if __name__ == "__main__":
    ingest_rh_excel()
