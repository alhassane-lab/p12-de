-- Silver model aggregating the last 12 months of activity at employee level.
select
    employee_id,
    extract(year from current_date) as activity_year,
    count(*) filter (
        where activity_date >= current_date - interval '365 days'
    ) as activity_count_12m,
    count(distinct activity_date) filter (
        where activity_date >= current_date - interval '365 days'
    ) as sport_days_count,
    max(activity_date) as last_activity_date
from {{ ref('sil_sport_activities') }}
where is_valid_activity
group by employee_id
