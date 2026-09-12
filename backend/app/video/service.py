from __future__ import annotations

import asyncio
import hashlib
import os
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import VideoStatus
from app.models.video import Video
from app.video.metadata import extract_metadata
from app.video.repository import VideoRepository
from app.video.storage import FileStorage


class VideoService:
    def __init__(self, session: AsyncSession, storage: FileStorage | None = None) -> None:
        self.session = session
        self.storage = storage or FileStorage()
        self.repository = VideoRepository(session)

    async def upload_video(self, upload: UploadFile) -> Video:
        if upload.filename is None:
            raise ValueError("Missing filename")
        if not upload.filename.lower().endswith((".mp4", ".mov", ".mkv")):
            raise ValueError("Unsupported video format")

        contents = await upload.read()
        if not contents:
            raise ValueError("Empty file")

        file_path, stored_name = self.storage.save_upload_from_bytes(contents, upload.filename)
        metadata = await extract_metadata(file_path)
        checksum = hashlib.sha256(contents).hexdigest()

        video = await self.repository.create(
            filename=stored_name,
            original_filename=upload.filename,
            duration_seconds=metadata["duration_seconds"],
            filesize=metadata["filesize"],
            width=metadata["width"],
            height=metadata["height"],
            fps=metadata["fps"],
            checksum=checksum,
            status=VideoStatus.READY,
        )
        return video

    async def list_videos(self) -> list[Video]:
        return await self.repository.list_all()

    async def get_video(self, video_id: str) -> Video | None:
        from uuid import UUID

        try:
            return await self.repository.get_by_id(UUID(video_id))
        except ValueError:
            return None

    async def assign_ready_video(self) -> Video | None:
        return await self.repository.get_ready_video()
