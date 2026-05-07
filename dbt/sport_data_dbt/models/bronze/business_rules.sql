-- Bronze model selecting the latest business rule version loaded from YAML.
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
        loaded_at,
        row_number() over (
            order by effective_from desc, loaded_at desc, rule_version desc
        ) as rn
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
    loaded_at
from ranked
where rn = 1
