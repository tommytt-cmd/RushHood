from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from app.events.event_bus import EventBus
from app.events.registry import registry
from app.events.channels import ALL_CHANNELS
from app.redis.client import RedisClient

logger = logging.getLogger("subscriber")


class Subscriber:
    def __init__(self, redis_client: RedisClient, event_bus: EventBus) -> None:
        self.redis_client = redis_client
        self.event_bus = event_bus
        self.handlers: dict[str, list[Callable[[Any], Any]]] = {}
        self._task: asyncio.Task | None = None
        self._stopping = False
        self._pubsub: Any | None = None

    def register_handler(self, event_name: str, handler: Callable[[Any], Any]) -> None:
        self.handlers.setdefault(event_name, []).append(handler)

    async def start(self) -> None:
        if self._task is not None:
            return
        self._pubsub = await self.redis_client.subscribe(*registry.all_channels())
        self._task = asyncio.create_task(self._listen())
        logger.info("subscriber_started", extra={"channels": registry.all_channels()})

    async def stop(self) -> None:
        self._stopping = True
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._pubsub is not None:
            try:
                await self._pubsub.unsubscribe(*registry.all_channels())
            except Exception:
                logger.exception("subscriber_unsubscribe_error")
        logger.info("subscriber_stopped")

    async def _listen(self) -> None:
        if self._pubsub is None:
            return
        while not self._stopping:
            message = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is None:
                await asyncio.sleep(0.1)
                continue
            data = message.get("data")
            channel = message.get("channel")
            if isinstance(data, bytes):
                raw = data.decode("utf-8")
            else:
                raw = str(data)
            try:
                event = self.event_bus.deserialize(raw)
                await self._dispatch(event)
                logger.info("event_received", extra={"event": event.event_name, "channel": channel})
            except Exception:
                logger.exception("event_deserialize_error", extra={"raw": raw})

    async def _dispatch(self, event: Any) -> None:
        handlers = self.handlers.get(event.event_name, [])
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.exception("event_handler_error", extra={"event": event.event_name})
