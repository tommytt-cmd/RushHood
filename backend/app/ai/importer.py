from __future__ import annotations

from typing import Iterable
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.replay_event import ReplayEvent


async def import_timeline(session: AsyncSession, video_id: str, timeline: Iterable[dict]) -> int:
    # timeline items expected as dicts with timestamp (seconds) and fields
    count = 0
    for item in timeline:
        ts = int(item.get("timestamp", 0) * 1000)
        ev = ReplayEvent(
            video_id=video_id,
            timestamp_ms=ts,
            vehicle_id=item.get("vehicle_id", ""),
            vehicle_type=item.get("vehicle_type", ""),
            direction=item.get("direction", ""),
            line_id=item.get("line_id", ""),
            cumulative_count=int(item.get("count", 0)),
        )
        session.add(ev)
        count += 1
    await session.commit()
    return count
