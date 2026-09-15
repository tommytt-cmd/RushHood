from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.repositories.stock_repository import StockRepository
from pydantic import BaseModel, Field, HttpUrl
from fastapi import status
import httpx
import json
import logging
from time import time

logger = logging.getLogger("stocks")

# Simple in-process cache fallback when Redis is not available. Maps key -> (expiry_ts, body_json)
_LOCAL_PRICE_CACHE: dict[str, tuple[float, dict]] = {}


router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/supported")
async def list_supported_stocks(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    """Return enabled stock tokens known to the backend for public display."""
    tokens = await StockRepository(session).list_enabled_tokens()
    return [
        {
            "address": token.token_address,
            "symbol": token.symbol,
            "name": token.name,
            "decimals": token.decimals,
            "logo_url": token.logo_url,
        }
        for token in tokens
]


@router.get("/prices/{symbol}")
async def get_stock_price(symbol: str, request: Request):
    """Proxy RHJ prices endpoint with server-side caching to avoid CORS and rate-limit issues.

    Returns the raw Robinhood JSON body under the same `quotes` structure.
    """
    if not symbol or not isinstance(symbol, str):
        raise HTTPException(status_code=400, detail="Invalid symbol")

    symbol_norm = symbol.strip().upper()
    if symbol_norm == "":
        raise HTTPException(status_code=400, detail="Empty symbol after trimming")
    # Basic validation: allow alphanumerics, dot, dash, underscore
    import re

    if not re.match(r"^[A-Z0-9._-]{1,32}$", symbol_norm):
        raise HTTPException(status_code=400, detail="Malformed symbol")

    cache_key = f"stock_price:{symbol_norm}"

    # Try Redis from app.state if available
    redis_client = getattr(request.app.state, "redis_client", None)
    # check redis usage
    try:
        if redis_client is not None and getattr(redis_client, "connected", False):
            # aioredis Redis instance is on redis_client._redis
            redis = getattr(redis_client, "_redis", None)
            if redis is not None:
                cached = await redis.get(cache_key)
                if cached:
                    try:
                        if isinstance(cached, (bytes, bytearray)):
                            cached = cached.decode()
                        body = json.loads(cached)
                        return body
                    except Exception:
                        # fallthrough to re-fetch if cache corrupt
                        logger.warning("corrupt_cache", extra={"key": cache_key})
    except Exception as exc:  # pragma: no cover - redis issues
        logger.warning("redis_cache_error", extra={"error": str(exc)})

    # Check local in-memory cache
    entry = _LOCAL_PRICE_CACHE.get(cache_key)
    if entry is not None:
        expiry, body = entry
        if expiry > time():
            return body
        else:
            del _LOCAL_PRICE_CACHE[cache_key]

    # Fetch from RHJ upstream
    url = f"https://api.robinhood.com/rhj/prices/{symbol_norm}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
        except httpx.ReadTimeout:
            logger.warning("rhj_timeout", extra={"symbol": symbol_norm})
            raise HTTPException(status_code=504, detail="Upstream timeout")
        except httpx.RequestError as exc:
            logger.warning("rhj_request_error", extra={"symbol": symbol_norm, "error": str(exc)})
            raise HTTPException(status_code=502, detail=f"Upstream request error: {exc}")

    # Map upstream status codes
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Price not found")
    if resp.status_code == 429:
        raise HTTPException(status_code=429, detail="Upstream rate limit")
    if resp.status_code >= 400:
        logger.warning("rhj_upstream_error", extra={"symbol": symbol_norm, "status": resp.status_code})
        raise HTTPException(status_code=502, detail=f"Upstream returned {resp.status_code}")

    try:
        body = resp.json()
    except Exception:
        logger.warning("rhj_invalid_json", extra={"symbol": symbol_norm})
        raise HTTPException(status_code=502, detail="Invalid JSON from upstream")

    # Cache the response for ~15 seconds
    ttl = 15
    try:
        if redis_client is not None and getattr(redis_client, "connected", False):
            redis = getattr(redis_client, "_redis", None)
            if redis is not None:
                await redis.set(cache_key, json.dumps(body), ex=ttl)
    except Exception as exc:  # pragma: no cover
        logger.warning("redis_set_error", extra={"error": str(exc)})

    # local fallback cache
    _LOCAL_PRICE_CACHE[cache_key] = (time() + ttl, body)

    return body



class StockCreate(BaseModel):
    address: str = Field(..., description="EVM contract address of the stock token")
    symbol: str = Field(..., max_length=32)
    name: str | None = Field(None, max_length=255)
    decimals: int = Field(..., ge=0, le=255)
    logo_url: HttpUrl | None = None
    enabled: bool = True


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_stock(
    payload: StockCreate,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    """Create or update a stock token for display and indexing."""
    repo = StockRepository(session)
    token = await repo.add_or_update_token(
        payload.address, payload.symbol, int(payload.decimals), payload.name, payload.logo_url, payload.enabled
    )
    return {
        "address": token.token_address,
        "symbol": token.symbol,
        "name": token.name,
        "decimals": token.decimals,
        "logo_url": token.logo_url,
        "enabled": token.enabled,
    }
