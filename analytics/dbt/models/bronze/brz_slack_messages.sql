-- Bronze model exposing raw simulated Slack messages for downstream reporting.
select
    message_id,
    process_date,
    activity_id,
    employee_id,
    channel_name,
    message_text,
    generated_at,
    status
from {{ source('raw', 'slack_messages_raw') }}
