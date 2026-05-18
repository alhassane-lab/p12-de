-- Bronze model selecting the latest business rule version loaded from YAML.
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
    loaded_at
from {{ ref('business_rules_validity') }}
where is_current
