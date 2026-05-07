-- Silver model joining employee master data with declarations and yearly activity metrics.
select
    e.employee_id,
    e.full_name,
    e.business_unit,
    e.gross_salary,
    e.transport_mode,
    e.distance_km_to_office,
    e.is_transport_mode_sportive,
    e.is_distance_rule_valid,
    d.declared_sport,
    coalesce(a.activity_count_12m, 0) as activity_count_12m,
    coalesce(a.sport_days_count, 0) as sport_days_count,
    a.last_activity_date
from {{ ref('sil_employees') }} e
left join {{ ref('sil_sport_declarations') }} d
    on e.employee_id = d.employee_id
left join {{ ref('sil_employee_activity_yearly') }} a
    on e.employee_id = a.employee_id
