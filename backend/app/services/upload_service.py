from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import VideoStatus
from app.models.timeline_event import TimelineEvent
from app.repositories.timeline_repository import TimelineRepository
from app.repositories.video_repository import VideoRepository
from app.storage.service import StorageService
from app.settings import settings


@dataclass
class UploadMetadata:
    video_id: str
    original_filename: str
    filename: str
    location_name: str
    country: Optional[str]
    duration_seconds: float
    filesize: int
    width: int
    height: int
    fps: float
    vehicle_total: int
    checksum: str
    processed_at: Optional[datetime]


class VideoUploadService:
    def __init__(self, session: AsyncSession, storage: StorageService) -> None:
        self.session = session
        self.storage = storage
        self.video_repository = VideoRepository(session)
        self.timeline_repository = TimelineRepository(session)

    async def upload_from_folder(self, folder_name: str) -> dict:
        folder = self._resolve_folder(folder_name)
        metadata_path = folder / "metadata.json"
        timeline_path = folder / "timeline.json"
        video_path = folder / "video.mp4"
        thumbnail_path = folder / "thumbnail.jpg"

        self._validate_required_files([video_path, metadata_path, timeline_path])

        metadata = self._load_metadata(metadata_path)
        events = self._load_timeline(timeline_path)

        self._verify_metadata(metadata)
        self._verify_timeline(events, metadata.vehicle_total)
        self._verify_checksum(video_path, metadata.checksum)

        if await self.video_repository.exists_by_video_id(metadata.video_id):
            raise ValueError("DuplicateVideoId")
        if await self.video_repository.exists_by_checksum(metadata.checksum):
            raise ValueError("DuplicateChecksum")

        await self.storage.ensure_bucket_exists()

        video_storage_key = await self.storage.upload_video(metadata.video_id, Path(metadata.filename).name, video_path.open("rb"))
        thumbnail_storage_key = None
        thumbnail_url = None
        if thumbnail_path.exists():
            thumbnail_storage_key = await self.storage.upload_thumbnail(metadata.video_id, thumbnail_path.name, thumbnail_path.open("rb"))
            thumbnail_url = await self.storage.generate_public_url(thumbnail_storage_key)

        video_url = await self.storage.generate_public_url(video_storage_key)
        storage_path = f"{metadata.video_id}/{Path(metadata.filename).name}"

        try:
            video = await self.video_repository.create(
                video_id=metadata.video_id,
                original_filename=metadata.original_filename,
                filename=metadata.filename,
                storage_path=storage_path,
                video_url=video_url,
                thumbnail_url=thumbnail_url,
                location_name=metadata.location_name,
                country=metadata.country,
                duration_seconds=int(metadata.duration_seconds),
                filesize=metadata.filesize,
                width=metadata.width,
                height=metadata.height,
                fps=metadata.fps,
                vehicle_total=metadata.vehicle_total,
                checksum=metadata.checksum,
                status=VideoStatus.READY,
                processed_at=metadata.processed_at,
                commit=False,
            )

            ev_objs = [TimelineEvent(video_id=video.id, timestamp_ms=int(ev["timestamp_ms"]), cumulative_count=int(ev["cumulative_count"])) for ev in events]
            await self.timeline_repository.bulk_create(ev_objs)
            await self.session.commit()
            await self.session.refresh(video)
        except Exception:
            await self.session.rollback()
            # cleanup uploaded files on failure
            try:
                await self.storage.delete_file(video_storage_key)
            except Exception:
                pass
            if thumbnail_storage_key:
                try:
                    await self.storage.delete_file(thumbnail_storage_key)
                except Exception:
                    pass
            raise

        return {
            "id": str(video.id),
            "video_id": video.video_id,
            "location_name": video.location_name,
            "vehicle_total": video.vehicle_total,
            "video_url": video.video_url,
            "thumbnail_url": video.thumbnail_url,
            "status": video.status,
        }

    def _resolve_folder(self, folder_name: str) -> Path:
        if ".." in folder_name or folder_name.startswith("/") or folder_name.startswith("\\"):
            raise ValueError("Invalid folder name")
        base = Path(settings.PROCESSED_VIDEO_DIRECTORY)
        folder = base / folder_name
        print(f"folder: {folder}")
        if not folder.exists() or not folder.is_dir():
            raise FileNotFoundError(f"Processed folder not found. {folder}")
        return folder

    def _validate_required_files(self, required_files: list[Path]) -> None:
        missing = [str(p.name) for p in required_files if not p.exists() or not p.is_file()]
        if missing:
            raise FileNotFoundError(f"Missing required files: {', '.join(missing)}")

    def _load_metadata(self, metadata_path: Path) -> UploadMetadata:
        try:
            raw = json.loads(metadata_path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid metadata JSON") from exc

        required = [
            "video_id",
            "original_filename",
            "filename",
            "location_name",
            "duration_seconds",
            "filesize",
            "width",
            "height",
            "fps",
            "vehicle_total",
            "checksum",
        ]
        missing = [field for field in required if field not in raw]
        if missing:
            raise ValueError(f"Invalid metadata: missing {', '.join(missing)}")

        processed_at = None
        if raw.get("processed_at"):
            try:
                processed_at = datetime.fromisoformat(str(raw["processed_at"]).replace("Z", "+00:00"))
            except Exception:
                processed_at = None

        return UploadMetadata(
            video_id=str(raw["video_id"]),
            original_filename=str(raw["original_filename"]),
            filename=str(raw["filename"]),
            location_name=str(raw["location_name"]),
            country=str(raw.get("country")) if raw.get("country") is not None else None,
            duration_seconds=float(raw["duration_seconds"]),
            filesize=int(raw["filesize"]),
            width=int(raw["width"]),
            height=int(raw["height"]),
            fps=float(raw["fps"]),
            vehicle_total=int(raw["vehicle_total"]),
            checksum=str(raw["checksum"]),
            processed_at=processed_at,
        )

    def _load_timeline(self, timeline_path: Path) -> list[dict]:
        try:
            raw = json.loads(timeline_path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid timeline JSON") from exc

        if not isinstance(raw, dict) or "events" not in raw or not isinstance(raw["events"], list):
            raise ValueError("Invalid timeline format")

        events = []
        for item in raw["events"]:
            if not isinstance(item, dict):
                raise ValueError("Invalid timeline event")
            timestamp = item.get("timestamp_ms")
            cumulative_count = item.get("cumulative_count")
            if not isinstance(timestamp, int) or not isinstance(cumulative_count, int):
                raise ValueError("Invalid timeline event values")
            events.append({"timestamp_ms": timestamp, "cumulative_count": cumulative_count})

        if not events:
            raise ValueError("Timeline must contain at least one event")

        return events

    def _verify_metadata(self, metadata: UploadMetadata) -> None:
        if not metadata.location_name:
            raise ValueError("Invalid metadata: location_name required")
        if metadata.duration_seconds <= 0:
            raise ValueError("Invalid metadata: duration_seconds must be > 0")
        if metadata.filesize < 0:
            raise ValueError("Invalid metadata: filesize must be >= 0")
        if metadata.width <= 0 or metadata.height <= 0:
            raise ValueError("Invalid metadata: width and height must be > 0")
        if metadata.fps <= 0:
            raise ValueError("Invalid metadata: fps must be > 0")
        if metadata.vehicle_total < 0:
            raise ValueError("Invalid metadata: vehicle_total must be >= 0")
        if not metadata.checksum:
            raise ValueError("Invalid metadata: checksum required")

    def _verify_timeline(self, events: list[dict], expected_total: int) -> None:
        last_count = 0
        last_timestamp = -1
        seen_timestamps = set()

        for event in events:
            timestamp = event["timestamp_ms"]
            count = event["cumulative_count"]

            if timestamp < 0:
                raise ValueError("Invalid timeline: timestamp_ms must be >= 0")
            if timestamp in seen_timestamps:
                raise ValueError("Invalid timeline: duplicate timestamps")
            seen_timestamps.add(timestamp)
            if timestamp <= last_timestamp:
                raise ValueError("Invalid timeline: timestamps must be increasing")

            if count != last_count + 1:
                raise ValueError("Invalid timeline: cumulative_count must increment sequentially starting at 1")

            last_timestamp = timestamp
            last_count = count

        if last_count != expected_total:
            raise ValueError("Invalid timeline: final cumulative_count must equal vehicle_total")

    def _verify_checksum(self, video_path: Path, expected_checksum: str) -> None:
        hash_sha256 = hashlib.sha256()
        with video_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                hash_sha256.update(chunk)
        actual_checksum = hash_sha256.hexdigest()
        if actual_checksum != expected_checksum:
            raise ValueError("Invalid checksum")
