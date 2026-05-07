-- Gold model exposing Slack messages as a reporting-ready table.
select
    message_id,
    activity_id,
    employee_id,
    channel_name,
    message_text,
    generated_at,
    status
from {{ ref('brz_slack_messages') }}
