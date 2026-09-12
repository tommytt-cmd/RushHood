from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.events.publisher import Publisher
from app.events.schemas import Heartbeat, HeartbeatPayload, ServerStatus, ServerStatusPayload
from app.websocket.manager import manager
from app.redis.client import RedisClient

logger = logging.getLogger("monitor")


class HeartbeatPublisher:
    def __init__(self, publisher: Publisher, interval_seconds: float = 5.0) -> None:
        self.publisher = publisher
        self.interval_seconds = interval_seconds
        self.server_id = str(uuid.uuid4())
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _run(self) -> None:
        while True:
            event = Heartbeat(event="heartbeat", payload=HeartbeatPayload(server_id=self.server_id))
            await self.publisher.publish(event)
            logger.info("heartbeat_published", extra={"server_id": self.server_id})
            await asyncio.sleep(self.interval_seconds)


class ServerStatusPublisher:
    def __init__(self, publisher: Publisher, redis_client: RedisClient, interval_seconds: float = 10.0) -> None:
        self.publisher = publisher
        self.redis_client = redis_client
        self.interval_seconds = interval_seconds
        self.start_time = datetime.now(timezone.utc)
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _run(self) -> None:
        while True:
            uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            status = ServerStatus(
                event="server_status",
                payload=ServerStatusPayload(
                    active_connections=manager.count(),
                    active_round=None,
                    uptime_seconds=uptime,
                    redis_connected=self.redis_client.connected,
                    server_time=datetime.now(timezone.utc),
                ),
            )
            await self.publisher.publish(status)
            logger.info("server_status_published", extra={"uptime_seconds": uptime})
            await asyncio.sleep(self.interval_seconds)
