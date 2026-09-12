from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import VideoStatus
from app.models.video import Video


class VideoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, filename: str, original_filename: str, duration_seconds: float, filesize: int, width: int, height: int, fps: float, checksum: str, status: VideoStatus = VideoStatus.READY) -> Video:
        video = Video(
            filename=filename,
            original_filename=original_filename,
            duration_seconds=int(duration_seconds),
            filesize=filesize,
            width=width,
            height=height,
            fps=fps,
            checksum=checksum,
            status=status,
        )
        self.session.add(video)
        await self.session.commit()
        await self.session.refresh(video)
        return video

    async def list_all(self) -> list[Video]:
        result = await self.session.execute(select(Video).order_by(Video.created_at.desc()))
        return list(result.scalars().all())

    async def get_by_id(self, video_id: UUID) -> Video | None:
        result = await self.session.execute(select(Video).where(Video.id == video_id))
        return result.scalar_one_or_none()

    async def get_ready_video(self) -> Video | None:
        result = await self.session.execute(select(Video).where(Video.status == VideoStatus.READY).order_by(Video.created_at.desc()))
        return result.scalar_one_or_none()
