"""Create and persist simulated Slack messages for consumed activities."""

import os
import uuid
from datetime import UTC, datetime

from pipeline.utils.db import db_cursor


def build_slack_message(activity: dict) -> dict:
    """Build the Slack-like payload associated with one sport activity."""
    channel = os.getenv("SLACK_CHANNEL", "#sport-avantages")
    message = (
        f":runner: Activite {activity['activity_type']} enregistree pour le salarie "
        f"{activity['employee_id']} le {activity['activity_date']} "
        f"({activity['distance_km']} km, {activity['duration_min']} min)."
    )
    return {
        "message_id": str(uuid.uuid4()),
        "process_date": activity.get("process_date", activity["activity_date"]),
        "activity_id": activity["activity_id"],
        "employee_id": activity["employee_id"],
        "channel_name": channel,
        "message_text": message,
        "generated_at": datetime.now(UTC),
        "status": "generated",
    }


def persist_slack_message(activity: dict) -> dict:
    """Store the simulated Slack message in the raw landing table."""
    payload = build_slack_message(activity)
    insert_sql = """
        insert into raw.slack_messages_raw (
            message_id, process_date, activity_id, employee_id, channel_name, message_text, generated_at, status
        ) values (
            %(message_id)s, %(process_date)s, %(activity_id)s, %(employee_id)s, %(channel_name)s, %(message_text)s, %(generated_at)s, %(status)s
        )
    """
    with db_cursor() as (conn, cur):
        cur.execute("alter table raw.slack_messages_raw add column if not exists process_date date")
        cur.execute(insert_sql, payload)
        conn.commit()
    return payload
