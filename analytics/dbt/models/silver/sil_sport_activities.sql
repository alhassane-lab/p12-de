-- Silver model cleaning and validating consumed sport activity events.
with deduplicated as (
    select
        *,
        row_number() over (
            partition by activity_id
            order by event_ts desc, offset_id desc
        ) as rn
    from {{ ref('brz_sport_activities') }}
),
cleaned as (
    select
        activity_id,
        employee_id,
        lower(activity_type) as activity_type,
        process_date,
        activity_date,
        distance_km,
        duration_min,
        calories_burned,
        source_system,
        event_ts,
        case
            when employee_id is null then false
            when activity_date is null then false
            when distance_km is null or distance_km < 0 then false
            when duration_min is null or duration_min <= 0 then false
            else true
        end as is_valid_activity
    from deduplicated
    where rn = 1
)
select
    c.activity_id,
    c.employee_id,
    c.activity_type,
    c.process_date,
    c.activity_date,
    c.distance_km,
    c.duration_min,
    c.calories_burned,
    c.source_system,
    c.event_ts,
    c.is_valid_activity,
    concat(
        ':runner: Activite ',
        c.activity_type,
        ' enregistree pour le salarie ',
        c.employee_id,
        ' le ',
        c.activity_date,
        ' (',
        c.distance_km,
        ' km, ',
        c.duration_min,
        ' min).'
    ) as slack_message_text
from cleaned c
