"""Create and persist simulated Slack messages for consumed activities."""

import os
import uuid
from datetime import UTC, datetime

from app.utils.db import db_cursor


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
            message_id, activity_id, employee_id, channel_name, message_text, generated_at, status
        ) values (
            %(message_id)s, %(activity_id)s, %(employee_id)s, %(channel_name)s, %(message_text)s, %(generated_at)s, %(status)s
        )
    """
    with db_cursor() as (conn, cur):
        cur.execute(insert_sql, payload)
        conn.commit()
    return payload
