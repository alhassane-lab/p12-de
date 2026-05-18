-- Bronze model exposing business rule validity windows derived from effective dates.
with ordered as (
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
            order by effective_from, loaded_at, rule_version
        ) as chronology_rank,
        lead(effective_from) over (
            order by effective_from, loaded_at, rule_version
        ) as next_effective_from
    from {{ ref('business_rules_history') }}
)
select
    rule_version,
    effective_from,
    case
        when chronology_rank = 1 then date '1900-01-01'
        else effective_from
    end as valid_from_inclusive,
    next_effective_from as effective_to_exclusive,
    office_address,
    bonus_rate,
    wellbeing_days,
    min_activities_per_year,
    max_km_walk_run,
    max_km_cycle_scooter_other,
    sportive_transport_modes,
    rules_payload,
    loaded_at,
    current_date >= effective_from
    and (next_effective_from is null or current_date < next_effective_from) as is_current
from ordered
