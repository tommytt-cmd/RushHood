from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.events.publisher import Publisher
from app.events.schemas import Heartbeat
from app.scheduler.scheduler import GameScheduler

logger = logging.getLogger("game")


class EventTimer:
    def __init__(self, scheduler: GameScheduler, publisher: Publisher) -> None:
        self.scheduler = scheduler
        self.publisher = publisher
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        heartbeat_counter = 0
        while True:
            await asyncio.sleep(1)
            await self.scheduler.tick()
            heartbeat_counter += 1
            if self.publisher is not None and heartbeat_counter % 15 == 0:
                heartbeat = Heartbeat(event="heartbeat", payload={"server_id": "rushhour-backend"})
                await self.publisher.publish(heartbeat)
            logger.info("timer_tick")
