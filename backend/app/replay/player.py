from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from app.replay.events import ReplayEvent


@dataclass
class Player:
    round_id: str
    events: List[ReplayEvent]
    started_at: datetime
    index: int = 0
    current_count: int = 0
    paused: bool = False
    finished: bool = False

    def elapsed_seconds(self, now: datetime) -> float:
        return (now - self.started_at).total_seconds()
