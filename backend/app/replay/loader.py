from __future__ import annotations

import json
from pathlib import Path
from typing import List

from app.replay.events import ReplayEvent, validate_event_obj
from app.video.storage import FileStorage


class ReplayLoadError(RuntimeError):
    pass


class ReplayLoader:
    def __init__(self, storage: FileStorage | None = None) -> None:
        self.storage = storage or FileStorage()
        self._cache: dict[str, List[ReplayEvent]] = {}

    def _events_filename_for(self, video_filename: str) -> str:
        p = Path(video_filename)
        return f"{p.stem}.events.json"

    def load(self, video_filename: str) -> List[ReplayEvent]:
        key = video_filename
        if key in self._cache:
            return self._cache[key]

        events_path = self.storage.base_dir / self._events_filename_for(video_filename)
        if not events_path.exists():
            raise ReplayLoadError("Missing replay file")

        try:
            raw = json.loads(events_path.read_text())
        except Exception as exc:
            raise ReplayLoadError(f"Malformed JSON: {exc}") from exc

        if not isinstance(raw, list):
            raise ReplayLoadError("Replay file must be a JSON array")

        events: List[ReplayEvent] = []
        seen_ts = set()
        for idx, obj in enumerate(raw):
            try:
                ev = validate_event_obj(obj)
            except Exception as exc:
                raise ReplayLoadError(f"Invalid event at index {idx}: {exc}") from exc
            if ev.timestamp in seen_ts:
                raise ReplayLoadError(f"Duplicate timestamp: {ev.timestamp}")
            seen_ts.add(ev.timestamp)
            events.append(ev)

        events.sort(key=lambda e: e.timestamp)
        self._cache[key] = events
        return events
