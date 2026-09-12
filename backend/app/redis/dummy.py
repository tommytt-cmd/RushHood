from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger("redis_dummy")


class DummyPubSub:
    def __init__(self, redis_client: "DummyRedisClient", channels: tuple[str, ...]) -> None:
        self._redis_client = redis_client
        self._channels: set[str] = set(channels)

    async def subscribe(self, *channels: str) -> None:
        self._channels.update(channels)
        logger.info("dummy_subscribe", extra={"channels": channels})

    async def unsubscribe(self, *channels: str) -> None:
        self._channels.difference_update(channels)
        logger.info("dummy_unsubscribe", extra={"channels": channels})

    async def get_message(self, ignore_subscribe_messages: bool = True, timeout: float = 1.0) -> Any:
        return await self._redis_client.get_message(self, timeout=timeout)


class DummyRedisClient:
    def __init__(self) -> None:
        self._connected = False
        self._messages: list[tuple[str, str]] = []
        self._condition = asyncio.Condition()
        self._pubsubs: set[DummyPubSub] = set()

    async def connect(self) -> None:
        logger.info("dummy_redis_connect")
        self._connected = True

    async def disconnect(self) -> None:
        logger.info("dummy_redis_disconnect")
        self._connected = False

    async def ping(self) -> bool:
        return True

    async def publish(self, channel: str, message: str) -> int:
        async with self._condition:
            self._messages.append((channel, message))
            self._condition.notify_all()
        # Avoid using reserved LogRecord keys (like 'message') in `extra`.
        # Use 'payload' instead so logging doesn't raise KeyError.
        logger.info("dummy_publish", extra={"channel": channel, "payload": message})
        return 1

    async def subscribe(self, *channels: str) -> Any:
        pubsub = DummyPubSub(self, channels)
        self._pubsubs.add(pubsub)
        await pubsub.subscribe(*channels)
        return pubsub

    async def get_message(self, pubsub: DummyPubSub, timeout: float = 1.0) -> Any:
        async with self._condition:
            deadline = asyncio.get_running_loop().time() + timeout if timeout is not None else None
            while True:
                for index, (channel, message) in enumerate(list(self._messages)):
                    if channel in pubsub._channels:
                        self._messages.pop(index)
                        return {"data": message, "channel": channel}
                if timeout is None:
                    await self._condition.wait()
                    continue
                remaining = deadline - asyncio.get_running_loop().time() if deadline is not None else timeout
                if remaining <= 0:
                    return None
                try:
                    await asyncio.wait_for(self._condition.wait(), timeout=remaining)
                except asyncio.TimeoutError:
                    return None

    @property
    def connected(self) -> bool:
        return self._connected
