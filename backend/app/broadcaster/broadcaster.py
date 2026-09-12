from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.websocket.manager import ConnectionManager

logger = logging.getLogger("game")


class Broadcaster:
    def __init__(self, manager: ConnectionManager) -> None:
        self.manager = manager

    async def publish(self, event: dict[str, Any]) -> None:
        logger.info("event_published", extra={"event": event.get("event")})
        await self.manager.broadcast(event)

    async def publish_status(self) -> None:
        await self.publish({"event": "server_status", "connections": self.manager.count()})
