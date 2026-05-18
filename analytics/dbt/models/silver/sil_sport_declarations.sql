-- Silver model keeping the latest declarative sport information per employee.
with deduplicated as (
    select
        *,
        row_number() over (
            partition by employee_id
            order by ingested_at desc, row_hash desc
        ) as rn
    from {{ ref('brz_sport_declarations') }}
)
select
    employee_id,
    nullif(trim(declared_sport), '') as declared_sport
from deduplicated
where rn = 1
