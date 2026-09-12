from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.domains.security.rate_limit import rate_limit_middleware, RateLimiter


def create_security_middleware(config: dict[str, dict[str, int]]):
    limiter = RateLimiter(config)

    async def security_middleware(request: Request, call_next):
        try:
            return await rate_limit_middleware(request, call_next, limiter)
        except Exception as exc:
            return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content={"detail": str(exc)})

    return security_middleware
