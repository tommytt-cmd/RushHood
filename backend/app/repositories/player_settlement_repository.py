from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player_settlement import PlayerSettlement


class PlayerSettlementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_round_and_wallet(self, round_id: UUID, wallet_address: str) -> PlayerSettlement | None:
        result = await self.session.execute(
            select(PlayerSettlement)
            .where(PlayerSettlement.round_id == round_id)
            .where(PlayerSettlement.wallet_address == wallet_address)
        )
        return result.scalar_one_or_none()

    async def list_by_round(self, round_id: UUID) -> list[PlayerSettlement]:
        result = await self.session.execute(
            select(PlayerSettlement).where(PlayerSettlement.round_id == round_id)
        )
        return list(result.scalars().all())

    async def list_by_wallet(self, wallet_address: str) -> list[PlayerSettlement]:
        result = await self.session.execute(
            select(PlayerSettlement).where(PlayerSettlement.wallet_address == wallet_address)
        )
        return list(result.scalars().all())

    async def create(self, settlement: PlayerSettlement) -> PlayerSettlement:
        self.session.add(settlement)
        await self.session.commit()
        await self.session.refresh(settlement)
        return settlement

    async def update(self, settlement: PlayerSettlement) -> PlayerSettlement:
        settlement.updated_at = datetime.now(timezone.utc)
        self.session.add(settlement)
        await self.session.commit()
        await self.session.refresh(settlement)
        return settlement

    async def create_or_update(self, settlement: PlayerSettlement) -> PlayerSettlement:
        existing = await self.get_by_round_and_wallet(settlement.round_id, settlement.wallet_address)
        if existing is None:
            return await self.create(settlement)

        existing.player_id = settlement.player_id
        existing.bet_prediction = settlement.bet_prediction
        existing.bet_stake = settlement.bet_stake
        existing.bet_status = settlement.bet_status
        existing.over_amount = settlement.over_amount
        existing.under_amount = settlement.under_amount
        existing.is_winner = settlement.is_winner
        existing.claim_status = settlement.claim_status
        existing.claimable_eth = settlement.claimable_eth
        existing.claimable_reward = settlement.claimable_reward
        existing.pending_eth = settlement.pending_eth
        existing.rush_claimed = settlement.rush_claimed
        existing.has_claimed = settlement.has_claimed
        existing.updated_at = settlement.updated_at
        return await self.update(existing)
