from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class BasePayload(BaseModel):
    pass


class BaseEvent(BaseModel):
    event_name: str = Field(..., alias="event")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: BasePayload

    model_config = {
        "populate_by_name": True,
        "extra": "forbid",
    }


class RoundCreatedPayload(BasePayload):
    round_id: str
    starts_at: datetime | None = None
    betting_closes_at: datetime | None = None
    threshold: int | None = None
    location_name: str | None = None

class PhaseChangePayload(BasePayload):
    phase: str
    roundId: str
    phaseStartTime: datetime | None = None
    phaseEndTime: datetime | None = None

class RoundStartedPayload(BasePayload):
    round_id: str
    round_number: int | None = None
    starts_at: datetime | None = None
    betting_closes_at: datetime | None = None
    locked_ends_at: datetime | None = None
    live_ends_at: datetime | None = None
    ends_at: datetime | None = None
    threshold: int | None = None
    location_name: str | None = None


class RoundLockedPayload(BasePayload):
    round_id: str


class RoundFinishedPayload(BasePayload):
    round_id: str
    result: int | None = None
    winner: str | None = None
    server_seed: str | None = None
    threshold: int | None = None

class RoundSettledPayload(BasePayload):
    round_id: str
    result: int 
    winner: str | None = None
    server_seed: str | None = None
    threshold: int | None = None

class ReplayTimelineEvent(BaseModel):
    timestamp_ms: int
    cumulative_count: int


class TimerUpdatedPayload(BasePayload):
    remaining: int


class VehicleDetectedPayload(BasePayload):
    vehicle_type: str
    direction: str
    count: int


class VehicleCountPayload(BasePayload):
    count: int
    timestamp_seconds: float | None = None


class ReplayStartedPayload(BasePayload):
    round_id: str
    video_url: str
    duration_seconds: float | None = None
    position_seconds: float | None = None
    timeline_events: list[ReplayTimelineEvent]
    location_name: str | None = None


class ReplayFinishedPayload(BasePayload):
    round_id: str
    final_count: int | None = None


class ProcessingProgressPayload(BasePayload):
    task: str
    progress: float


class ServerStatusPayload(BasePayload):
    active_connections: int
    active_round: str | None = None
    uptime_seconds: float
    redis_connected: bool
    server_time: datetime


class HeartbeatPayload(BasePayload):
    server_id: str | None = None


class BetPlacedPayload(BasePayload):
    wallet_address: str
    prediction: int
    stake: int


class SettlementCompletedPayload(BasePayload):
    round_id: str
    status: str


class PlayerSettlementUpdatedPayload(BasePayload):
    round_id: str
    wallet_address: str
    bet_prediction: int | None = None
    bet_stake: int | None = None
    bet_status: str | None = None
    over_amount: int | None = None
    under_amount: int | None = None
    is_winner: bool | None = None
    claim_status: str | None = None
    claimable_eth: int | None = None
    claimable_reward: int | None = None
    pending_eth: int | None = None
    rush_claimed: bool | None = None
    has_claimed: bool


class PhaseChange(BaseEvent):
    event_name: Literal["phase_change"] = Field("phase_change", alias="event")
    payload: PhaseChangePayload

class RoundCreated(BaseEvent):
    event_name: Literal["round_created"] = Field("round_created", alias="event")
    payload: RoundCreatedPayload

class RoundStarted(BaseEvent):
    event_name: Literal["round_started"] = Field("round_started", alias="event")
    payload: RoundStartedPayload


class RoundLocked(BaseEvent):
    event_name: Literal["round_locked"] = Field("round_locked", alias="event")
    payload: RoundLockedPayload


class RoundFinished(BaseEvent):
    event_name: Literal["round_finished"] = Field("round_finished", alias="event")
    payload: RoundFinishedPayload

class RoundSettled(BaseEvent):
    event_name: Literal["round_settled"] = Field("round_settled", alias="event")
    payload: RoundSettledPayload

class TimerUpdated(BaseEvent):
    event_name: Literal["timer"] = Field("timer", alias="event")
    payload: TimerUpdatedPayload


class VehicleDetected(BaseEvent):
    event_name: Literal["vehicle_detected"] = Field("vehicle_detected", alias="event")
    payload: VehicleDetectedPayload


class VehicleCount(BaseEvent):
    event_name: Literal["vehicle_count"] = Field("vehicle_count", alias="event")
    payload: VehicleCountPayload


class ReplayStarted(BaseEvent):
    event_name: Literal["replay_started"] = Field("replay_started", alias="event")
    payload: ReplayStartedPayload


class ReplayFinished(BaseEvent):
    event_name: Literal["replay_finished"] = Field("replay_finished", alias="event")
    payload: ReplayFinishedPayload


class ProcessingProgress(BaseEvent):
    event_name: Literal["processing_progress"] = Field("processing_progress", alias="event")
    payload: ProcessingProgressPayload


class ServerStatus(BaseEvent):
    event_name: Literal["server_status"] = Field("server_status", alias="event")
    payload: ServerStatusPayload


class Heartbeat(BaseEvent):
    event_name: Literal["heartbeat"] = Field("heartbeat", alias="event")
    payload: HeartbeatPayload


class BetPlaced(BaseEvent):
    event_name: Literal["bet_placed"] = Field("bet_placed", alias="event")
    payload: BetPlacedPayload


class SettlementCompleted(BaseEvent):
    event_name: Literal["settlement_completed"] = Field("settlement_completed", alias="event")
    payload: SettlementCompletedPayload


class PlayerSettlementUpdated(BaseEvent):
    event_name: Literal["player_settlement_updated"] = Field("player_settlement_updated", alias="event")
    payload: PlayerSettlementUpdatedPayload
