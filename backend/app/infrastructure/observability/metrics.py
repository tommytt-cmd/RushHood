from __future__ import annotations

import time
from collections import Counter, defaultdict
from threading import Lock
from typing import Any


class MetricsCollector:
    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: Counter[str] = Counter()
        self._latencies: defaultdict[str, list[float]] = defaultdict(list)
        self._gauges: dict[str, float] = {}

    def increment(self, name: str, value: int = 1) -> None:
        with self._lock:
            self._counters[name] += value

    def observe_latency(self, name: str, duration_seconds: float) -> None:
        with self._lock:
            self._latencies[name].append(duration_seconds)

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = value

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "latencies": {k: list(v) for k, v in self._latencies.items()},
            }


metrics = MetricsCollector()
