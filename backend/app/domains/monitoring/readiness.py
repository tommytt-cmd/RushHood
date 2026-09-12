from __future__ import annotations

from typing import Any


class ReadinessChecker:
    def __init__(self, db_check: Any | None = None, redis_check: Any | None = None, scheduler_check: Any | None = None) -> None:
        self.db_check = db_check
        self.redis_check = redis_check
        self.scheduler_check = scheduler_check

    async def check(self) -> dict[str, Any]:
        checks = {
            "database": await self._run(self.db_check),
            "redis": await self._run(self.redis_check),
            "scheduler": await self._run(self.scheduler_check),
        }
        return checks

    async def _run(self, func: Any | None) -> bool:
        if func is None:
            return True
        try:
            result = func()
            if hasattr(result, "__await__"):
                result = await result
            return bool(result)
        except Exception:
            return False
