from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.ai.jobs import job_manager

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}")
async def job_status(job_id: str):
    status = job_manager.get_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": status.status.value, "progress": status.progress, "current_frame": status.current_frame, "estimated_seconds_remaining": status.estimated_seconds_remaining}
