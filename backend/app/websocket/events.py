from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    event: str


class RoundStartedEvent(BaseEvent):
    event: Literal["round_started"] = "round_started"
    round_id: UUID
    starts_at: str


class VideoStartedEvent(BaseEvent):
    event: Literal["video_started"] = "video_started"
    round_id: UUID
    video_id: UUID
    filename: str
    video_url: str
    duration_seconds: int
    starts_at: str
    server_time: str


class VideoSyncEvent(BaseEvent):
    event: Literal["video_sync"] = "video_sync"
    round_id: UUID
    video_id: UUID
    filename: str
    video_url: str
    duration_seconds: int
    position_seconds: float
    starts_at: str
    server_time: str
    status: str


class TimerUpdatedEvent(BaseEvent):
    event: Literal["timer"] = "timer"
    remaining: int


class BetPlacedEvent(BaseEvent):
    event: Literal["bet_placed"] = "bet_placed"
    total_bets: int


class BettingLockedEvent(BaseEvent):
    event: Literal["betting_locked"] = "betting_locked"


class RoundFinishedEvent(BaseEvent):
    event: Literal["round_finished"] = "round_finished"
    result: int


class ServerStatusEvent(BaseEvent):
    event: Literal["server_status"] = "server_status"
    connections: int
