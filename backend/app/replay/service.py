from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.replay.events import ReplayEvent
from app.replay.repository import ReplayRepository, ReplayState
from app.repositories.timeline_repository import TimelineRepository

logger = logging.getLogger("replay")


class ReplayService:
    """
    Runtime replay engine.

    Responsibilities:

    - Load timeline events from PostgreSQL.
    - Maintain replay state in memory.
    - Keep the replay synchronized with the video.
    - Support pause/resume/stop.
    """

    def __init__(
        self,
        session_factory: Any,
        timeline_repository: TimelineRepository,
    ) -> None:
        self.session_factory = session_factory
        self.timeline_repository = timeline_repository
        self.repo = ReplayRepository()

    async def load(self, video_id: str) -> list[ReplayEvent]:
        """
        Load replay events from the database.
        """
        events = await self.timeline_repository.get_by_video(video_id)

        logger.info(
            "replay_loaded",
            extra={
                "video_id": video_id,
                "events": len(events),
            },
        )

        return events

    async def start(
        self,
        round_id: str,
        video_id: str,
        starts_at: datetime | None = None,
        video_duration_seconds: float | None = None,
    ) -> None:
        """
        Start a replay for a round.
        """

        events = await self.load(video_id)

        started_at = self._as_utc(
            starts_at or datetime.now(timezone.utc)
        )

        fallback_duration = (
            events[-1].timestamp_ms
            if events
            else 0.0
        )

        duration = float(
            video_duration_seconds
            or fallback_duration
        )

        state = ReplayState(
                round_id=round_id,
                video_id=video_id,
                started_at=started_at,
                events=events,
                video_duration_seconds=max(duration, fallback_duration),
            )

        self.repo.add(state)

        logger.info(
            "replay_started",
            extra={
                "round_id": round_id,
                "video_id": video_id,
                "events": len(events),
            },
        )

    def stop(self, round_id: str) -> None:
        state = self.repo.get(round_id)

        if state is None:
            return

        state.finished = True

        self.repo.remove(round_id)

        logger.info(
            "replay_stopped",
            extra={
                "round_id": round_id,
            },
        )

    def pause(self, round_id: str) -> None:
        state = self.repo.get(round_id)

        if state is None:
            return

        if state.paused:
            return

        state.paused = True
        state.paused_at = datetime.now(timezone.utc)

        logger.info(
            "replay_paused",
            extra={
                "round_id": round_id,
            },
        )

    def resume(self, round_id: str) -> None:
        state = self.repo.get(round_id)

        if state is None:
            return

        if not state.paused:
            return

        now = datetime.now(timezone.utc)

        if state.paused_at is not None:
            state.total_paused_seconds += (
                now - state.paused_at
            ).total_seconds()

        state.paused_at = None
        state.paused = False

        logger.info(
            "replay_resumed",
            extra={
                "round_id": round_id,
            },
        )

    def get_current_count(
        self,
        round_id: str | None = None,
    ) -> int | None:
        state = self._state_for(round_id)

        if state is None:
            return None

        return state.current_count

    def get_sync_payload(
        self,
        round_id: str,
        now: datetime | None = None,
    ) -> dict[str, float | int] | None:
        state = self.repo.get(round_id)

        if state is None:
            return None

        current_time = self._as_utc(
            now or datetime.now(timezone.utc)
        )

        return {
            "count": state.current_count,
            "elapsed": round(
                state.elapsed_seconds(current_time),
                3,
            ),
        }

    def get_state(
        self,
        round_id: str,
    ) -> ReplayState | None:
        return self.repo.get(round_id)

    def _state_for(
        self,
        round_id: str | None,
    ) -> ReplayState | None:
        if round_id is not None:
            return self.repo.get(round_id)

        active = self.repo.list_active()

        if not active:
            return None

        return active[0]

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc,
            )

        return value.astimezone(timezone.utc)