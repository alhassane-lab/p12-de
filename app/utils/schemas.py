"""Small typed payload definitions used by the streaming layer."""

from dataclasses import dataclass


@dataclass
class ActivityEvent:
    """Canonical shape of a simulated activity event."""
    activity_id: str
    employee_id: str
    activity_type: str
    activity_date: str
    distance_km: float
    duration_min: int
    calories_burned: int
    source_system: str
    event_ts: str
