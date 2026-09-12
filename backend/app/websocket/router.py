from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from app.api.dependencies import get_round_service, get_video_service, get_replay_service
from app.core.enums import RoundStatus
from app.replay.service import ReplayService
from app.services.round_service import RoundService
from app.video.service import VideoService
from app.websocket.manager import ConnectionManager, manager

logger = logging.getLogger("game")
router = APIRouter(tags=["websocket"])


def get_connection_manager() -> ConnectionManager:
    return manager


async def _send_video_sync(
    websocket: WebSocket,
    round_service: RoundService,
    video_service: VideoService,
    replay_service: ReplayService | None,
) -> None:
    current = await round_service.get_current_round()
    if current is None or current.video_id is None or current.status not in {
        RoundStatus.OPEN,
        RoundStatus.LOCKED,
        RoundStatus.LIVE,
    }:
        return

    video = await video_service.get_video(str(current.video_id))
    if video is None:
        return

    now = datetime.now(timezone.utc)
    # Playback starts when the live phase begins, not when betting opens.
    starts_at = (
        current.locked_ends_at
        if current.status == RoundStatus.LIVE and current.locked_ends_at is not None
        else current.starts_at
    ) or now
    position_seconds = max(0.0, (now - starts_at).total_seconds())

    payload = {
        "event": "video_sync",
        "round_id": str(current.id),
        "video_id": str(video.id),
        "filename": video.filename,
        "video_url": video.video_url,
        "duration_seconds": video.duration_seconds,
        "position_seconds": round(position_seconds, 3),
        "starts_at": starts_at.isoformat(),
        "server_time": now.isoformat(),
        "status": current.status,
    }
    await manager.send_to(websocket, payload)
    if replay_service is None:
        return
    replay_sync = replay_service.get_sync_payload(str(current.id), now=now)
    if replay_sync is not None:
        await manager.send_to(websocket, {"event": "replay_sync", **replay_sync})


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    manager: ConnectionManager = Depends(get_connection_manager),
    round_service: RoundService = Depends(get_round_service),
    video_service: VideoService = Depends(get_video_service),
    replay_service: ReplayService | None = Depends(get_replay_service),
) -> None:
    await manager.connect(websocket)
    try:
        await _send_video_sync(websocket, round_service, video_service, replay_service)
        while websocket.client_state == WebSocketState.CONNECTED:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.exception("websocket_error", extra={"error": str(exc)})
        manager.disconnect(websocket)
