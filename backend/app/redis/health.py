from __future__ import annotations

from fastapi import APIRouter
from app.redis.client import RedisClient

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/redis")
async def redis_health() -> dict[str, object]:
    client = RedisClient()
    return {"redis": await client.ping()}


@router.get("")
async def health() -> dict[str, object]:
    client = RedisClient()
    return {"status": "healthy", "redis": await client.ping()}
