from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any

from fastapi import HTTPException, Request, status

logger = logging.getLogger("security")


class RateLimitExceeded(Exception):
    pass


class RateLimiter:
    def __init__(self, config: dict[str, int]) -> None:
        self.config = config
        self.requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup(self, key: str, window: int) -> None:
        now = time.time()
        self.requests[key] = [timestamp for timestamp in self.requests[key] if timestamp > now - window]

    def check(self, key: str, limit: int, window: int) -> None:
        self._cleanup(key, window)
        if len(self.requests[key]) >= limit:
            raise RateLimitExceeded(f"Rate limit exceeded for {key}")
        self.requests[key].append(time.time())
        logger.info("rate_limit_check", extra={"key": key, "limit": limit, "window": window})

    def enforce(self, request: Request, route_name: str) -> None:
        limit_config = self.config.get(route_name)
        if limit_config is None:
            return
        limit = limit_config.get("limit", 10)
        window = limit_config.get("window", 60)
        client_ip = request.client.host if request.client else "unknown"
        key = f"{route_name}:{client_ip}"
        self.check(key, limit, window)


async def rate_limit_middleware(request: Request, call_next: Any, limiter: RateLimiter) -> Any:
    try:
        route_name = request.scope.get("path", "unknown")
        limiter.enforce(request, route_name)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))
    return await call_next(request)
