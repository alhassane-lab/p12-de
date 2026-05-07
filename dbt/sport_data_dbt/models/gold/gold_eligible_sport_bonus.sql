-- Gold model computing employee eligibility for the 5% sport bonus.
with rules as (
    select *
    from {{ ref('business_rules') }}
),
base as (
    select *
    from {{ ref('sil_employee_activity_joined') }}
)
select
    b.employee_id,
    extract(year from current_date) as reference_year,
    b.full_name,
    b.business_unit,
    b.gross_salary,
    r.bonus_rate,
    round((b.gross_salary * r.bonus_rate)::numeric, 2) as bonus_amount,
    b.transport_mode,
    b.distance_km_to_office,
    case
        when b.is_transport_mode_sportive and b.is_distance_rule_valid then true
        else false
    end as eligibility_status,
    case
        when not b.is_transport_mode_sportive then 'transport_non_sportif'
        when not b.is_distance_rule_valid then 'distance_hors_regle'
        else 'eligible'
    end as eligibility_reason,
    r.rule_version
from base b
cross join rules r
