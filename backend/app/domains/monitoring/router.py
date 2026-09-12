from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.domains.monitoring.diagnostics import DiagnosticsCollector
from app.domains.monitoring.health import HealthChecker
from app.domains.monitoring.metrics import MonitoringMetrics
from app.domains.monitoring.readiness import ReadinessChecker
from app.infrastructure.observability.metrics import metrics

router = APIRouter(tags=["monitoring"])

health_checker = HealthChecker()
readiness_checker = ReadinessChecker()
diagnostics_collector = DiagnosticsCollector()


@router.get("/health")
async def health() -> dict[str, object]:
    checks = {"database": True, "redis": True, "scheduler": True}
    status = health_checker.build_status(checks)
    return {
        "status": status.status,
        "application_version": status.application_version,
        "uptime": status.uptime_seconds,
    }


@router.get("/ready")
async def ready() -> dict[str, object]:
    checks = await readiness_checker.check()
    status = "READY" if all(checks.values()) else "NOT_READY"
    return {"status": status, "checks": checks}


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ALIVE"}


@router.get("/metrics")
async def metrics_endpoint() -> dict[str, object]:
    return MonitoringMetrics.snapshot()


@router.get("/api/v1/admin/diagnostics")
async def diagnostics() -> dict[str, object]:
    return diagnostics_collector.collect()
