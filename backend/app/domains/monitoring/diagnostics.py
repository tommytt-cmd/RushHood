from __future__ import annotations

from typing import Any


class DiagnosticsCollector:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def collect(self) -> dict[str, Any]:
        return {
            "config": {k: v for k, v in self.config.items() if not str(k).startswith("SECRET")},
            "dependencies": {
                "database": self.config.get("database_enabled", True),
                "redis": self.config.get("redis_enabled", True),
                "scheduler": self.config.get("scheduler_enabled", True),
            },
        }
