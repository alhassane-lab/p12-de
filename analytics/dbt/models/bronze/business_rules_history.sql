-- Bronze model exposing the full history of loaded business rule versions.
with ranked as (
    select
        rule_version,
        effective_from,
        office_address,
        bonus_rate,
        wellbeing_days,
        min_activities_per_year,
        max_km_walk_run,
        max_km_cycle_scooter_other,
        sportive_transport_modes,
        rules_payload,
        loaded_at,
        row_number() over (
            order by effective_from desc, loaded_at desc, rule_version desc
        ) as recency_rank
    from {{ source('raw', 'business_rules_raw') }}
)
select
    rule_version,
    effective_from,
    office_address,
    bonus_rate,
    wellbeing_days,
    min_activities_per_year,
    max_km_walk_run,
    max_km_cycle_scooter_other,
    sportive_transport_modes,
    rules_payload,
    loaded_at,
    recency_rank = 1 as is_latest
from ranked
