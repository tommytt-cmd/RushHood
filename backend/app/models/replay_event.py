from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ReplayEvent(Base):
    __tablename__ = "replay_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    video_id: Mapped[UUID] = mapped_column(String(36), nullable=False)
    timestamp_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    vehicle_id: Mapped[str] = mapped_column(String(64), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(32), nullable=False)
    direction: Mapped[str] = mapped_column(String(32), nullable=True)
    line_id: Mapped[str] = mapped_column(String(64), nullable=True)
    cumulative_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
