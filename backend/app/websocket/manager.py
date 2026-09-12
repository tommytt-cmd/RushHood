from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketState

logger = logging.getLogger("game")


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        if websocket.client_state != WebSocketState.CONNECTED:
            await websocket.accept()
        self._connections.add(websocket)
        logger.info("client_connected", extra={"connections": self.count()})

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)
        logger.info("client_disconnected", extra={"connections": self.count()})

    async def broadcast(self, payload: dict[str, Any]) -> None:
        message = json.dumps(payload)
        dead: list[WebSocket] = []
        for websocket in list(self._connections):
            try:
                await websocket.send_text(message)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(websocket)
        logger.info("event_broadcast", extra={"event": payload.get("event"), "connections": self.count()})

    async def send_to(self, websocket: WebSocket, payload: dict[str, Any]) -> None:
        try:
            await websocket.send_text(json.dumps(payload))
        except Exception:
            self.disconnect(websocket)

    def count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()
