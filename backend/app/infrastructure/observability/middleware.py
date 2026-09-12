from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.infrastructure.observability.metrics import metrics
from app.infrastructure.observability.tracing import set_request_id

logger = logging.getLogger("app")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Any:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        set_request_id(request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            metrics.increment("http_requests_total", 1)
            metrics.increment(f"http_status_{500}", 1)
            logger.exception("request_failed", extra={"request_id": request_id, "route": request.url.path, "event": "request_failed"})
            raise
        duration = time.perf_counter() - start
        metrics.increment("http_requests_total", 1)
        metrics.increment(f"http_status_{response.status_code}", 1)
        metrics.observe_latency("http_latency_seconds", duration)
        logger.info(
            "request_completed",
            extra={"request_id": request_id, "route": request.url.path, "event": "request_completed", "duration": round(duration, 4)},
        )
        response.headers["x-request-id"] = request_id
        return response
