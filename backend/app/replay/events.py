from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ReplayEvent:
    """
    A replay timeline event.

    Represents the moment the cumulative vehicle count
    should be updated during video playback.
    """

    timestamp_ms: int
    cumulative_count: int

    @property
    def timestamp(self) -> float:
        """
        Timestamp expressed in seconds for playback logic.
        """
        return self.timestamp_ms / 1000.0


def validate_event_obj(obj: Any) -> ReplayEvent:
    """
    Validate a replay event loaded from timeline.json
    or reconstructed from the database.
    """

    if not isinstance(obj, dict):
        raise ValueError("Replay event must be an object")

    required = {
        "timestamp_ms",
        "cumulative_count",
    }

    missing = required.difference(obj)

    if missing:
        raise ValueError(
            f"Missing fields: {', '.join(sorted(missing))}"
        )

    try:
        timestamp_ms = int(obj["timestamp_ms"])
        cumulative_count = int(obj["cumulative_count"])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid replay event: {exc}"
        ) from exc

    if timestamp_ms < 0:
        raise ValueError(
            "timestamp_ms must be >= 0"
        )

    if cumulative_count <= 0:
        raise ValueError(
            "cumulative_count must be > 0"
        )

    return ReplayEvent(
        timestamp_ms=timestamp_ms,
        cumulative_count=cumulative_count,
    )