from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.repositories.stock_repository import StockRepository


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
