from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


@dataclass
class ProcessingProgress:
    job_id: str
    status: JobStatus
    progress: int = 0
    current_frame: int = 0
    total_frames: int = 0
    estimated_seconds_remaining: Optional[float] = None


@dataclass
class Detection:
    x1: int
    y1: int
    x2: int
    y2: int
    score: float
    class_name: str


@dataclass
class Track:
    track_id: int
    vehicle_id: str
    bbox: tuple[int, int, int, int]
    class_name: str


@dataclass
class TimelineEvent:
    timestamp: float
    event_id: str
    vehicle_id: str
    vehicle_type: str
    direction: str
    line_id: str
    count: int
