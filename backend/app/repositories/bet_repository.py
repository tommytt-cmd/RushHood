from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import BetStatus
from app.models.bet import Bet
from app.models.player import Player


class BetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        round_id: UUID,
        player_id: UUID,
        prediction: int,
        stake: int,
        transaction_hash: str | None = None,
        onchain_round_number: int | None = None,
    ) -> Bet:
        bet = Bet(
            round_id=round_id,
            player_id=player_id,
            prediction=prediction,
            stake=stake,
            transaction_hash=transaction_hash,
            onchain_round_number=onchain_round_number,
            status=BetStatus.PENDING,
        )
        self.session.add(bet)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        await self.session.refresh(bet)
        return bet

    async def get_by_transaction_hash(self, transaction_hash: str) -> Bet | None:
        result = await self.session.execute(
            select(Bet).where(Bet.transaction_hash == transaction_hash.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_round_and_player(self, round_id: UUID, wallet_address: str) -> Bet | None:
        normalized_wallet = wallet_address.strip().lower()
        result = await self.session.execute(
            select(Bet)
            .join(Player, Bet.player_id == Player.id)
            .where(Bet.round_id == round_id, func.lower(Player.wallet_address) == normalized_wallet)
        )
        return result.scalar_one_or_none()

    async def list_by_round(self, round_id: UUID) -> list[Bet]:
        result = await self.session.execute(select(Bet).where(Bet.round_id == round_id).order_by(Bet.created_at.desc()))
        return list(result.scalars().all())

    async def list_by_player(self, wallet_address: str) -> list[Bet]:
        normalized_wallet = wallet_address.strip().lower()
        result = await self.session.execute(
            select(Bet)
            .join(Player, Bet.player_id == Player.id)
            .where(func.lower(Player.wallet_address) == normalized_wallet)
        )
        return list(result.scalars().all())

    async def update(self, bet: Bet) -> Bet:
        self.session.add(bet)
        await self.session.commit()
        await self.session.refresh(bet)
        return bet
