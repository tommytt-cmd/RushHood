from __future__ import annotations

from typing import Any, Callable, Dict, Type

from app.events.channels import EVENT_CHANNEL_MAP
from app.events.schemas import BaseEvent


class EventRegistry:
    def __init__(self) -> None:
        self._events: Dict[str, Type[BaseEvent]] = {}
        self._channels: Dict[str, str] = {}

    def register(self, event_name: str, event_type: Type[BaseEvent]) -> None:
        self._events[event_name] = event_type
        self._channels[event_name] = EVENT_CHANNEL_MAP.get(event_name, "game_events")

    def get_event_type(self, event_name: str) -> Type[BaseEvent] | None:
        return self._events.get(event_name)

    def channel_for(self, event_name: str) -> str:
        if event_name not in self._channels:
            raise ValueError(f"No channel configured for event '{event_name}'")
        return self._channels[event_name]

    def all_channels(self) -> list[str]:
        return list(set(self._channels.values()))


registry = EventRegistry()


def register_event(event_type: Type[BaseEvent]) -> Type[BaseEvent]:
    # try common locations for the declared event name (string, Field default, or Pydantic model_fields)
    event_name = getattr(event_type, "event_name", None)
    # if it's a FieldInfo or similar, try to extract default
    if event_name is not None and not isinstance(event_name, str):
        # attempt to pull a default attribute (pydantic Field)
        default = getattr(event_name, "default", None)
        if isinstance(default, str):
            event_name = default
        else:
            event_name = None

    # fallback: inspect pydantic v2 model_fields for an alias 'event' or name 'event_name'
    if event_name is None:
        model_fields = getattr(event_type, "model_fields", None)
        if isinstance(model_fields, dict):
            for fname, finfo in model_fields.items():
                alias = getattr(finfo, "alias", None)
                if alias == "event" or fname in ("event", "event_name"):
                    default = getattr(finfo, "default", None)
                    if isinstance(default, str):
                        event_name = default
                        break

    if event_name is None:
        raise ValueError("Event type must define event_name")
    registry.register(event_name, event_type)
    return event_type
