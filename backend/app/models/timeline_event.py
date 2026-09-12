from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    video_id: Mapped[UUID] = mapped_column(nullable=False)
    timestamp_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    cumulative_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(),
)
