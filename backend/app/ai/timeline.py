from __future__ import annotations

from typing import List
from app.ai.schemas import TimelineEvent


def build_timeline(events: List[dict]) -> List[TimelineEvent]:
    # events are dicts with timestamp, vehicle_id, vehicle_type, direction, line_id, count
    items = []
    for i, e in enumerate(events):
        te = TimelineEvent(
            timestamp=float(e["timestamp"]),
            event_id=e.get("event_id", f"evt_{i:06d}"),
            vehicle_id=e.get("vehicle_id", ""),
            vehicle_type=e.get("vehicle_type", ""),
            direction=e.get("direction", ""),
            line_id=e.get("line_id", ""),
            count=int(e.get("count", 0)),
        )
        items.append(te)
    items.sort(key=lambda t: t.timestamp)
    return items
