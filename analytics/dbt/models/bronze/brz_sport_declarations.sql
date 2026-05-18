-- Bronze model exposing raw sport declaration rows with light normalization.
select
    ingestion_id,
    ingested_at,
    process_date,
    source_file,
    employee_id,
    trim(declared_sport) as declared_sport,
    row_hash
from {{ source('raw', 'sport_declarations_raw') }}
