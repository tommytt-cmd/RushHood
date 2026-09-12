from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable

from app.ai.schemas import TimelineEvent


def export_timeline(timeline: Iterable[TimelineEvent], out_path: str) -> str:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # ensure ordered
    items = sorted(list(timeline), key=lambda t: t.timestamp)
    data = [t.__dict__ for t in items]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    return str(path)


def export_metadata(metadata: dict, out_path: str) -> str:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata["processed_at"] = time.time()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)
    return str(path)
