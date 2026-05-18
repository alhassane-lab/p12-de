-- Monitoring view exposing daily data flow volumes across pipeline layers.
with raw_events as (
    select
        process_date,
        count(*) as raw_event_count
    from {{ ref('brz_sport_activities') }}
    group by process_date
),
silver_activities as (
    select
        process_date,
        count(*) as silver_activity_count,
        count(*) filter (where is_valid_activity) as valid_activity_count,
        count(*) filter (where not is_valid_activity) as invalid_activity_count,
        count(distinct employee_id) filter (where is_valid_activity) as active_employee_count
    from {{ ref('sil_sport_activities') }}
    group by process_date
),
gold_timeline as (
    select
        snapshot_date as activity_date,
        count(*) filter (where activity_count_on_date > 0) as employee_snapshots_with_activity,
        sum(activity_count_on_date) as total_activities_on_date,
        count(*) filter (where is_wellbeing_eligible) as wellbeing_eligible_employee_count
    from {{ ref('gold_employee_benefit_timeline') }}
    group by snapshot_date
)
select
    coalesce(r.process_date, s.process_date, g.activity_date) as metric_date,
    coalesce(r.raw_event_count, 0) as raw_event_count,
    coalesce(s.silver_activity_count, 0) as silver_activity_count,
    coalesce(s.valid_activity_count, 0) as valid_activity_count,
    coalesce(s.invalid_activity_count, 0) as invalid_activity_count,
    coalesce(s.active_employee_count, 0) as active_employee_count,
    coalesce(g.employee_snapshots_with_activity, 0) as employee_snapshots_with_activity,
    coalesce(g.total_activities_on_date, 0) as total_activities_on_date,
    coalesce(g.wellbeing_eligible_employee_count, 0) as wellbeing_eligible_employee_count
from raw_events r
full outer join silver_activities s
    on r.process_date = s.process_date
full outer join gold_timeline g
    on coalesce(r.process_date, s.process_date) = g.activity_date
