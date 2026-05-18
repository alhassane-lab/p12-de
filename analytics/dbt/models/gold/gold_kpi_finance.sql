-- Gold KPI model aggregating executive finance and activity indicators.
with bonus as (
    select
        count(*) filter (where eligibility_status) as eligible_bonus_employees,
        round(coalesce(sum(bonus_amount) filter (where eligibility_status), 0)::numeric, 2) as total_bonus_cost,
        round(coalesce(avg(bonus_amount) filter (where eligibility_status), 0)::numeric, 2) as avg_bonus_amount
    from {{ ref('gold_eligible_sport_bonus') }}
),
wellbeing as (
    select
        count(*) filter (where eligibility_status) as eligible_wellbeing_employees
    from {{ ref('gold_eligible_wellbeing_days') }}
),
activities as (
    select
        count(*) filter (where is_valid_activity) as activity_count_total
    from {{ ref('sil_sport_activities') }}
)
select
    -- This table is intentionally aggregated to a single row per reference year
    -- so BI tools can use it directly for executive KPI cards.
    extract(year from current_date) as reference_year,
    bonus.eligible_bonus_employees,
    wellbeing.eligible_wellbeing_employees,
    bonus.total_bonus_cost,
    bonus.avg_bonus_amount,
    activities.activity_count_total
from bonus
cross join wellbeing
cross join activities
