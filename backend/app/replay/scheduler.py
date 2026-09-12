from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from app.events.publisher import Publisher
from app.events.schemas import ReplayFinished, VehicleCount
from app.replay.service import ReplayService

logger = logging.getLogger("replay")


class ReplayScheduler:
    """
    Background replay loop.

    Responsibilities:

    - Advance active replay states.
    - Emit vehicle_count events.
    - Emit replay_finished when playback completes.

    It does NOT load timeline data or interact with the database.
    """

    def __init__(
        self,
        replay_service: ReplayService,
        publisher: Publisher | None = None,
    ) -> None:
        self.replay_service = replay_service
        self.publisher = publisher
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is None:
            return

        self._task.cancel()

        try:
            await self._task
        except asyncio.CancelledError:
            pass

        self._task = None

    async def _run(self) -> None:
        while True:
            await asyncio.sleep(0.1)
            await self._tick()

    async def _tick(self) -> None:
        now = datetime.now(timezone.utc)

        for state in self.replay_service.repo.list_active():

            if state.finished or state.paused:
                continue

            elapsed = state.elapsed_seconds(now)

            events = state.events
            index = state.index
            #print(f"Index: {index}, Events: {len(events)}, Event index timestamp: {events[index].timestamp_ms} Elaps: {elapsed} Loop: {index < len(events) and events[index].timestamp_ms <= elapsed}")
            
            
            try:
                while (
                    index < len(events)
                    and events[index].timestamp_ms <= elapsed
                ):
                    event = events[index]
                    #print(f"Event cumulative count: {event.cumulative_count} \nState cumulative count: {state.current_count}")

                    if event.cumulative_count > state.current_count:
                        state.current_count = event.cumulative_count

                        if self.publisher:
                            await self.publisher.publish(
                                VehicleCount(
                                    event="vehicle_count",
                                    payload={
                                        "round_id": state.round_id,
                                        "count": event.cumulative_count,
                                        "timestamp_seconds": round(
                                            event.timestamp_ms,
                                            3,
                                        ),
                                    },
                                )
                            )

                        logger.info(
                            "vehicle_count",
                            extra={
                                "round_id": state.round_id,
                                "count": event.cumulative_count,
                                "timestamp": event.timestamp_ms,
                            },
                        )

                    index += 1
            except Exception as exc:
                print(f"Vehicle count error: {exc}")  

            state.index = index

            if (
                elapsed >= state.video_duration_seconds
                or index >= len(events)
            ):
                state.finished = True

                if self.publisher:
                    await self.publisher.publish(
                        ReplayFinished(
                            event="replay_finished",
                            payload={
                                "round_id": state.round_id,
                                "final_count": state.current_count,
                            },
                        )
                    )
                    

                logger.info(
                    "replay_finished",
                    extra={
                        "round_id": state.round_id,
                        "final_count": state.current_count,
                    },
                )
                