from __future__ import annotations

from app.events.registry import registry, register_event
from app.events.schemas import (
    BaseEvent,
    BasePayload,
    BetPlaced,
    Heartbeat,
    ProcessingProgress,
    ReplayFinished,
    ReplayStarted,
    RoundCreated,
    RoundFinished,
    RoundSettled,
    RoundLocked,
    RoundStarted,
    PhaseChange,
    ServerStatus,
    SettlementCompleted,
    PlayerSettlementUpdated,
    TimerUpdated,
    VehicleCount,
    VehicleDetected,
)

for event_cls in [
    PhaseChange,
    RoundCreated,
    RoundStarted,
    RoundLocked,
    RoundFinished,
    RoundSettled,
    TimerUpdated,
    VehicleDetected,
    VehicleCount,
    ReplayStarted,
    ReplayFinished,
    ProcessingProgress,
    ServerStatus,
    Heartbeat,
    BetPlaced,
    SettlementCompleted,
    PlayerSettlementUpdated,
]:
    register_event(event_cls)

__all__ = [
    "registry",
    "register_event",
    "BaseEvent",
    "BasePayload",
    "BetPlaced",
    "Heartbeat",
    "ProcessingProgress",
    "ReplayFinished",
    "ReplayStarted",
    "PhaseChange"
    "RoundCreated",
    "RoundFinished",
    "RoundSettled",
    "RoundLocked",
    "RoundStarted",
    "ServerStatus",
    "SettlementCompleted",
    "PlayerSettlementUpdated",
    "TimerUpdated",
    "VehicleCount",
    "VehicleDetected",
]
