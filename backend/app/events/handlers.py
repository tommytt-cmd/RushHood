from __future__ import annotations

from typing import Any

from app.broadcaster.broadcaster import Broadcaster
from app.events.event_bus import EventBus
from app.events.registry import registry


def create_broadcaster_handler(broadcaster: Broadcaster) -> Any:
    async def handle(event: Any) -> None:
        await broadcaster.publish(_websocket_payload(event))

    return handle


def _websocket_payload(event: Any) -> dict[str, Any]:
    return event.model_dump(mode="json", by_alias=True)


def register_broadcaster_handlers(broadcaster: Broadcaster, subscriber: Any) -> None:
    handler = create_broadcaster_handler(broadcaster)
    for event_name in registry._events.keys():
        subscriber.register_handler(event_name, handler)
