from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.models.video import Video
from app.video.service import VideoService
from app.video.storage import FileStorage
from fastapi import BackgroundTasks, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.jobs import job_manager, JobManager
from app.api.dependencies import get_session

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/local/upload", response_model=dict[str, object], status_code=status.HTTP_201_CREATED)
async def upload_video(file: UploadFile = File(...), session: AsyncSession = Depends(get_session)) -> dict[str, object]:
    service = VideoService(session)
    try:
        video = await service.upload_video(file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"id": str(video.id), "filename": video.filename, "duration": video.duration_seconds, "status": video.status.value}


@router.get("", response_model=list[dict[str, object]])
async def list_videos(session: AsyncSession = Depends(get_session)) -> list[dict[str, object]]:
    service = VideoService(session)
    videos = await service.list_videos()
    return [{"id": str(video.id), "filename": video.filename, "duration": video.duration_seconds, "status": video.status.value} for video in videos]

def _parse_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    if not range_header.startswith("bytes="):
        raise ValueError("Invalid Range header")
    range_value = range_header[len("bytes="):].strip()
    start_str, end_str = range_value.split("-", 1)

    if start_str == "":
        end = file_size - 1
        start = file_size - int(end_str)
    else:
        start = int(start_str)
        end = int(end_str) if end_str else file_size - 1

    if start < 0 or end < start or end >= file_size:
        raise ValueError("Range out of bounds")
    return start, end


async def _file_iterator(file_path: str, start: int, end: int, chunk_size: int = 8192) -> AsyncIterator[bytes]:
    with open(file_path, "rb") as handle:
        handle.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            chunk = handle.read(min(chunk_size, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


@router.get("/files/{filename}", response_model=None)
async def stream_video(filename: str, request: Request):
    safe_name = Path(filename).name
    storage = FileStorage()
    if not storage.exists(safe_name):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found")

    file_path = storage.get_path(safe_name)
    file_size = Path(file_path).stat().st_size
    media_type, _ = mimetypes.guess_type(safe_name)
    range_header = request.headers.get("range")

    if range_header:
        try:
            start, end = _parse_range_header(range_header, file_size)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail=str(exc)) from exc

        headers = {
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(end - start + 1),
        }
        return StreamingResponse(
            _file_iterator(file_path, start, end),
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            media_type=media_type or "application/octet-stream",
            headers=headers,
        )

    return FileResponse(
        file_path,
        media_type=media_type or "application/octet-stream",
        headers={"Accept-Ranges": "bytes"},
    )

@router.get("/{video_id}", response_model=dict[str, object])
async def get_video(video_id: str, session: AsyncSession = Depends(get_session)) -> dict[str, object]:
    service = VideoService(session)
    video = await service.get_video(video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return {"id": str(video.id), "filename": video.filename, "duration": video.duration_seconds, "status": video.status.value}


@router.post("/{video_id}/process", response_model=dict[str, str])
async def process_video(video_id: str, request: Request, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    # resolve video id -> filename via DB
    from app.video.service import VideoService

    service = VideoService(session)
    video = await service.get_video(video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    filename = video.filename
    publisher = getattr(request.app.state, "publisher", None)
    JobManager(publisher=publisher)
    job_id = await job_manager.start_processing(filename)
    return {"job_id": job_id}


@router.get("/jobs/{job_id}")
async def job_status(job_id: str):
    status = job_manager.get_status(job_id)
    if status is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {"status": status.status.value, "progress": status.progress, "current_frame": status.current_frame, "estimated_seconds_remaining": status.estimated_seconds_remaining}
