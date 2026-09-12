from __future__ import annotations

import logging
from typing import Any

from app.events.event_bus import EventBus
from app.events.schemas import BaseEvent

logger = logging.getLogger("publisher")


class Publisher:
    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus

    async def publish(self, event: BaseEvent) -> None:
        try:
            await self.event_bus.publish(event)
            logger.info("published_event", extra={"event": event.event_name})
        except Exception as exc:
            logger.exception("publish_failed", extra={"event": event.event_name, "error": str(exc)})
            raise
