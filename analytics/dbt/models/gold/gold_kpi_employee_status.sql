-- Gold model exposing one row per employee for BI drill-down and filtering.
select
    e.employee_id,
    e.full_name,
    e.business_unit,
    e.contract_type,
    b.eligibility_status as is_bonus_eligible,
    b.bonus_amount,
    b.potential_bonus_amount,
    b.eligibility_reason as bonus_reason,
    w.eligibility_status as is_wellbeing_eligible,
    w.wellbeing_days_awarded,
    w.eligibility_reason as wellbeing_reason,
    e.activity_count_12m,
    e.last_activity_date,
    e.last_process_date,
    e.transport_mode,
    e.distance_km_to_office
from {{ ref('sil_employee_activity_joined') }} e
left join {{ ref('gold_eligible_sport_bonus') }} b
    on e.employee_id = b.employee_id
left join {{ ref('gold_eligible_wellbeing_days') }} w
    on e.employee_id = w.employee_id
