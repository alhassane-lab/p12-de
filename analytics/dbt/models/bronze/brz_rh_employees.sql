-- Bronze model exposing the raw HR employee landing table with light trimming only.
select
    ingestion_id,
    ingested_at,
    process_date,
    source_file,
    employee_id,
    trim(last_name) as last_name,
    trim(first_name) as first_name,
    birth_date_raw,
    trim(business_unit) as business_unit,
    hire_date_raw,
    gross_salary_raw,
    trim(contract_type) as contract_type,
    cp_days_raw,
    trim(home_address) as home_address,
    trim(declared_transport_mode) as declared_transport_mode,
    row_hash
from {{ source('raw', 'rh_employees_raw') }}
