from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class HealthStatus:
    status: str
    application_version: str
    uptime_seconds: float
    checks: dict[str, Any]


class HealthChecker:
    def __init__(self, started_at: datetime | None = None) -> None:
        self.started_at = started_at or datetime.now(timezone.utc)

    def get_uptime_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self.started_at).total_seconds()

    def build_status(self, checks: dict[str, Any]) -> HealthStatus:
        return HealthStatus(
            status="healthy" if all(checks.values()) else "degraded",
            application_version="0.1.0",
            uptime_seconds=self.get_uptime_seconds(),
            checks=checks,
        )
