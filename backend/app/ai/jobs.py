from __future__ import annotations

import asyncio
import uuid
from typing import Dict, Optional

from app.ai.schemas import JobStatus, ProcessingProgress
from app.ai.processor import VideoProcessor
from app.video.storage import FileStorage
from app.events.publisher import Publisher
from app.events.schemas import ProcessingProgress as ProcessingProgressEvent, ProcessingProgressPayload


class ProcessingJob:
    def __init__(self, job_id: str, video_db_id: str, video_filename: str):
        self.job_id = job_id
        self.video_db_id = video_db_id
        self.video_filename = video_filename
        self.status = JobStatus.queued
        self.progress = 0
        self.current_frame = 0
        self.total_frames = 0
        self._task: Optional[asyncio.Task] = None


class JobManager:
    _instance: "JobManager" | None = None

    def __new__(cls, publisher: Publisher | None = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, publisher: Publisher | None = None):
        self.jobs: Dict[str, ProcessingJob] = {}
        self._publisher = publisher
        self._lock = asyncio.Lock()

    async def start_processing(self, video_db_id: str, video_filename: str | None = None, model_path: str | None = None, lines: Dict | None = None) -> str:
        async with self._lock:
            # prevent multiple jobs for same video
            for j in self.jobs.values():
                if getattr(j, "video_db_id", None) == video_db_id and j.status in (JobStatus.queued, JobStatus.running):
                    raise RuntimeError("Processing already running for this video")
            job_id = str(uuid.uuid4())
            job = ProcessingJob(job_id, video_db_id, video_filename or video_db_id)
            self.jobs[job_id] = job
            job._task = asyncio.create_task(self._run(job, model_path, lines))
            return job_id

    async def _run(self, job: ProcessingJob, model_path: str | None, lines: Dict | None) -> None:
        job.status = JobStatus.running
        storage = FileStorage()
        # resolve video path
        # video_id expected to be filename for now
        video_filename = getattr(job, "video_filename", job.video_db_id)
        video_path = storage.get_path(video_filename)
        processor = VideoProcessor(model_path=model_path, lines=lines)
        try:
            result = processor.process(video_path, out_dir=storage.get_dir())
            # import timeline into DB
            try:
                import json
                from app.ai.importer import import_timeline
                from app.database.session import SessionLocal

                timeline_path = result.get("timeline")
                if timeline_path:
                    with open(timeline_path, "r", encoding="utf-8") as fh:
                        timeline_list = json.load(fh)
                    async with SessionLocal() as session:
                        await import_timeline(session, str(job.video_db_id), timeline_list)
            except Exception:
                # log but don't fail the job import step
                pass
            job.status = JobStatus.completed
            job.progress = 100
            # publish completion event
            if self._publisher is not None:
                ev = ProcessingProgressEvent(event="processing_progress", payload=ProcessingProgressPayload(task=job.video_id, progress=100.0))
                await self._publisher.publish(ev)
        except asyncio.CancelledError:
            job.status = JobStatus.cancelled
        except Exception:
            job.status = JobStatus.failed

    def get_status(self, job_id: str) -> Optional[ProcessingProgress]:
        job = self.jobs.get(job_id)
        if job is None:
            return None
        return ProcessingProgress(job_id=job.job_id, status=job.status, progress=job.progress, current_frame=job.current_frame, total_frames=job.total_frames)


job_manager = JobManager()
