from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.redis.config import RedisConfig

logger = logging.getLogger("redis")

try:
    import redis.asyncio as aioredis
    from redis import exceptions as redis_exceptions
except ImportError:  # pragma: no cover
    aioredis = None  # type: ignore[assignment]
    redis_exceptions = None  # type: ignore[assignment]


class RedisClient:
    _instance: RedisClient | None = None

    def __new__(cls, config: RedisConfig | None = None) -> RedisClient:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: RedisConfig | None = None) -> None:
        self.config = config or RedisConfig()
        self._redis: Any | None = None
        self._connected = False
        self._lock = asyncio.Lock()
        self._reconnect_count = 0

    async def connect(self) -> None:
        if self._connected and self._redis is not None:
            return
        if aioredis is None:  # pragma: no cover
            raise RuntimeError("redis.asyncio is not installed")

        async with self._lock:
            if self._connected and self._redis is not None:
                return
            logger.info("redis_connect_attempt", extra={"host": self.config.host, "port": self.config.port, "db": self.config.db})
            options = {
                "host": self.config.host,
                "port": self.config.port,
                "db": self.config.db,
                "password": self.config.password,
                "decode_responses": False,
                "socket_keepalive": True,
                "max_connections": self.config.pool_max_connections,
            }
            if self.config.url:
                self._redis = aioredis.from_url(self.config.url, **options)
            else:
                self._redis = aioredis.Redis(**options)
            try:
                await self._redis.ping()
                self._connected = True
                logger.info("redis_connected")
            except Exception as exc:
                self._redis = None
                raise RuntimeError("Redis connect failed") from exc

    async def disconnect(self) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.close()
        except Exception:
            logger.exception("redis_disconnect_error")
        finally:
            self._redis = None
            self._connected = False
            logger.info("redis_disconnected")

    async def ping(self) -> bool:
        try:
            await self.connect()
            if self._redis is None:
                return False
            await self._redis.ping()
            return True
        except Exception:
            self._connected = False
            return False

    async def publish(self, channel: str, message: str) -> int:
        if self._redis is None or not self._connected:
            await self.connect()
        try:
            assert self._redis is not None
            start = asyncio.get_running_loop().time()
            result = await self._redis.publish(channel, message)
            latency_ms = (asyncio.get_running_loop().time() - start) * 1000
            logger.info("redis_publish", extra={"channel": channel, "latency_ms": latency_ms})
            return result
        except Exception as exc:
            logger.warning("redis_publish_error", extra={"channel": channel, "error": str(exc)})
            await self._attempt_reconnect()
            assert self._redis is not None
            return await self._redis.publish(channel, message)

    async def subscribe(self, *channels: str) -> Any:
        if self._redis is None or not self._connected:
            await self.connect()
        assert self._redis is not None
        pubsub = self._redis.pubsub(ignore_subscribe_messages=True)
        await pubsub.subscribe(*channels)
        logger.info("redis_subscribed", extra={"channels": channels})
        return pubsub

    async def _attempt_reconnect(self) -> None:
        if aioredis is None:  # pragma: no cover
            raise RuntimeError("redis.asyncio is not installed")
        self._reconnect_count += 1
        logger.info("redis_reconnect_attempt", extra={"reconnect_count": self._reconnect_count})
        await asyncio.sleep(self.config.reconnect_interval)
        await self.disconnect()
        await self.connect()

    @property
    def reconnect_count(self) -> int:
        return self._reconnect_count

    @property
    def connected(self) -> bool:
        return self._connected
