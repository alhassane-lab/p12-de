-- Gold model dedicated to BI map visualizations with one row per employee.
select
    e.employee_id,
    e.full_name,
    e.business_unit,
    e.contract_type,
    regexp_replace(trim(split_part(e.home_address, ',', 2)), '^[0-9]{5}[[:space:]]+', '') as home_city,
    e.home_lat,
    e.home_lon,
    e.distance_km_to_office,
    k.is_bonus_eligible,
    k.is_wellbeing_eligible
from {{ ref('sil_employees') }} e
left join {{ ref('gold_kpi_employee_status') }} k
    on e.employee_id = k.employee_id
