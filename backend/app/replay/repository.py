from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from app.replay.events import ReplayEvent


@dataclass(slots=True)
class ReplayState:
    """
    Runtime replay state for a single game round.

    This state exists only in memory while a replay is active.
    """

    round_id: str
    video_id: str

    started_at: datetime

    events: list[ReplayEvent]

    video_duration_seconds: float

    index: int = 0

    current_count: int = 0

    paused: bool = False

    finished: bool = False

    paused_at: datetime | None = None

    total_paused_seconds: float = 0.0

    @property
    def current_index(self) -> int:
        return self.index

    @current_index.setter
    def current_index(self, value: int) -> None:
        self.index = value

    @property
    def total_events(self) -> int:
        return len(self.events)

    @property
    def is_complete(self) -> bool:
        return self.finished or self.index >= len(self.events)

    def elapsed_seconds(self, now: datetime) -> float:
        """
        Returns the replay playback position, excluding paused time.
        """
        paused_seconds = self.total_paused_seconds

        if self.paused and self.paused_at is not None:
            paused_seconds += (
                now - self.paused_at
            ).total_seconds()

        return max(
            0.0,
            (now - self.started_at).total_seconds()
            - paused_seconds,
        )


class ReplayRepository:
    """
    In-memory store of active replay states.

    Key:
        round_id

    Value:
        ReplayState
    """

    def __init__(self) -> None:
        self._store: Dict[str, ReplayState] = {}

    def add(self, state: ReplayState) -> None:
        self._store[state.round_id] = state

    def get(self, round_id: str) -> ReplayState | None:
        return self._store.get(round_id)

    def exists(self, round_id: str) -> bool:
        return round_id in self._store

    def remove(self, round_id: str) -> None:
        self._store.pop(round_id, None)

    def clear(self) -> None:
        self._store.clear()

    def list_active(self) -> list[ReplayState]:
        return [
            state
            for state in self._store.values()
            if not state.finished
        ]

    def list_all(self) -> list[ReplayState]:
        return list(self._store.values())   