from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime, timezone

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.timeline_event import TimelineEvent


class TimelineRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_create(self, events: list[TimelineEvent]) -> None:
        if not events:
            return
        payload = []
        for event in events:
            eid = getattr(event, "id", None) or uuid4()
            #created_at = getattr(event, "created_at", None) or datetime.now(timezone.utc)
            payload.append(
                {
                    "id": eid,
                    "video_id": event.video_id,
                    "timestamp_ms": event.timestamp_ms,
                    "cumulative_count": event.cumulative_count,
                }
            )
        stmt = insert(TimelineEvent).values(payload)
        await self.session.execute(stmt)

    async def get_by_video(self, video_id: UUID) -> list[TimelineEvent]:
        result = await self.session.execute(select(TimelineEvent).where(TimelineEvent.video_id == video_id).order_by(TimelineEvent.timestamp_ms))
        return list(result.scalars().all())
