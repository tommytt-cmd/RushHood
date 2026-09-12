from __future__ import annotations

import logging
from typing import Any

from app.redis.client import RedisClient

logger = logging.getLogger("redis")


class RedisLifecycle:
    def __init__(self, client: RedisClient) -> None:
        self.client = client

    async def startup(self) -> None:
        try:
            await self.client.connect()
        except Exception:
            logger.exception("redis_startup_failed")

    async def shutdown(self) -> None:
        try:
            await self.client.disconnect()
        except Exception:
            logger.exception("redis_shutdown_failed")
