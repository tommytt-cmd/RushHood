from __future__ import annotations

import json
import logging
from typing import Any

from app.events.registry import registry
from app.events.schemas import BaseEvent

logger = logging.getLogger("event_bus")


class EventBus:
    def __init__(self, redis_client: Any, registry: Any) -> None:
        self.redis_client = redis_client
        self.registry = registry

    async def publish(self, event: BaseEvent) -> None:
        event_name = event.event_name
        if self.registry.get_event_type(event_name) is None:
            raise ValueError(f"Unknown event type: {event_name}")
        channel = self.registry.channel_for(event_name)
        payload = event.model_dump(by_alias=True)
        message = json.dumps(payload, default=str)
        if self.redis_client is None:
            logger.info("event_published_no_redis", extra={"event": event_name, "channel": channel})
            return
        await self.redis_client.publish(channel, message)
        logger.info("event_published", extra={"event": event_name, "channel": channel})

    def deserialize(self, raw_data: str) -> BaseEvent:
        try:
            payload = json.loads(raw_data)
        except json.JSONDecodeError as exc:
            logger.warning("deserialize_failed", extra={"error": str(exc)})
            raise
        event_name = payload.get("event")
        event_type = self.registry.get_event_type(event_name)
        if event_type is None:
            raise ValueError(f"Unknown event type: {event_name}")
        return event_type.model_validate(payload)
