from __future__ import annotations

from app.infrastructure.observability.metrics import metrics


class MonitoringMetrics:
    @staticmethod
    def snapshot() -> dict[str, object]:
        return metrics.snapshot()
