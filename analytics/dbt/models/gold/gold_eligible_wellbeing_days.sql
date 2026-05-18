-- Gold model computing employee eligibility for wellbeing leave days.
with rules as (
    select *
    from {{ ref('business_rules_validity') }}
    where current_date >= effective_from
      and (effective_to_exclusive is null or current_date < effective_to_exclusive)
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
    b.activity_count_12m,
    case
        when b.activity_count_12m >= r.min_activities_per_year then r.wellbeing_days
        else 0
    end as wellbeing_days_awarded,
    case
        when b.activity_count_12m >= r.min_activities_per_year then true
        else false
    end as eligibility_status,
    case
        when b.activity_count_12m >= r.min_activities_per_year then 'eligible'
        else 'insufficient_activities'
    end as eligibility_reason,
    r.rule_version
from base b
cross join rules r
