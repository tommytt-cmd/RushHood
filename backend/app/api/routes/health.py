from __future__ import annotations

from fastapi import APIRouter, Request

from app.settings import settings
from app.websocket.manager import manager

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health(request: Request) -> dict[str, object]:
    client = getattr(request.app.state, "redis_client", None)
    redis_ok = False
    if client is not None:
        try:
            redis_ok = await client.ping()
        except Exception:
            pass
    oracle_ok = False
    if settings.ORACLE_ENABLED:
        oracle_client = getattr(request.app.state, "oracle_client", None)
        if oracle_client is not None:
            try:
                oracle_ok = oracle_client.is_connected()
            except Exception:
                oracle_ok = False
    return {
        "status": "healthy",
        "redis": redis_ok,
        "oracle": oracle_ok,
        "uptime": 0,
        "connections": manager.count(),
    }


@router.get("/redis")
async def redis_health(request: Request) -> dict[str, object]:
    client = getattr(request.app.state, "redis_client", None)
    return {
        "status": "healthy",
        "redis": await client.ping() if client is not None else False,
    }


@router.get("/events")
async def events_health(request: Request) -> dict[str, object]:
    client = getattr(request.app.state, "redis_client", None)
    return {
        "status": "healthy",
        "redis": await client.ping() if client is not None else False,
        "channels": ["game_events", "timer_events", "vehicle_events", "processing_events", "admin_events", "server_events", "heartbeat_events"],
    }
