from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import VideoStatus
from app.database.base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    video_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    video_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(Text, nullable=True)
    location_name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(255), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    filesize: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    fps: Mapped[float] = mapped_column(Float, nullable=False)
    vehicle_total: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=VideoStatus.UPLOADING.value,
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
