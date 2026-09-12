from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player import Player


class PlayerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, wallet_address: str) -> Player:
        normalized_wallet = wallet_address.strip().lower()
        result = await self.session.execute(
            select(Player).where(func.lower(Player.wallet_address) == normalized_wallet)
        )
        player = result.scalar_one_or_none()
        if player is not None:
            return player

        player = Player(wallet_address=normalized_wallet)
        self.session.add(player)
        await self.session.commit()
        await self.session.refresh(player)
        return player

    async def get_by_wallet(self, wallet_address: str) -> Player | None:
        normalized_wallet = wallet_address.strip().lower()
        result = await self.session.execute(
            select(Player).where(func.lower(Player.wallet_address) == normalized_wallet)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, player_id: UUID) -> Player | None:
        return await self.session.get(Player, player_id)
