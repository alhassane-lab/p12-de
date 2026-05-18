-- Bronze model extracting typed columns from the raw Redpanda JSON payload.
select
    event_id as activity_id,
    process_date,
    topic,
    partition_id,
    offset_id,
    event_ts,
    consumed_at,
    payload_json,
    payload_json ->> 'employee_id' as employee_id,
    payload_json ->> 'activity_type' as activity_type,
    cast(payload_json ->> 'activity_date' as date) as activity_date,
    cast(payload_json ->> 'distance_km' as numeric(10, 2)) as distance_km,
    cast(payload_json ->> 'duration_min' as integer) as duration_min,
    cast(payload_json ->> 'calories_burned' as integer) as calories_burned,
    payload_json ->> 'source_system' as source_system,
    payload_json ->> 'process_date' as payload_process_date
from {{ source('raw', 'sport_activities_stream_raw') }}
