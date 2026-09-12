from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player import Player
from app.models.round import Round
from app.models.stock import (
    RoundStock,
    StockClaim,
    StockIndexerCheckpoint,
    StockReward,
    StockToken,
)


class StockRepository:
    """Persistence for indexed StockVault data; it never submits transactions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_last_indexed_block(self, vault_address: str) -> int | None:
        result = await self.session.execute(
            select(StockIndexerCheckpoint.last_indexed_block).where(
                StockIndexerCheckpoint.vault_address == vault_address.lower()
            )
        )
        return result.scalar_one_or_none()

    async def set_last_indexed_block(self, vault_address: str, block_number: int) -> None:
        """Record completed work only after all events in its range were handled."""
        vault_address = vault_address.lower()
        checkpoint = await self.session.get(StockIndexerCheckpoint, vault_address)
        if checkpoint is None:
            checkpoint = StockIndexerCheckpoint(
                vault_address=vault_address,
                last_indexed_block=block_number,
            )
            self.session.add(checkpoint)
        else:
            checkpoint.last_indexed_block = block_number
        await self.session.commit()

    async def get_token(self, address: str) -> StockToken | None:
        result = await self.session.execute(select(StockToken).where(StockToken.token_address == address.lower()))
        return result.scalar_one_or_none()

    async def get_or_create_token(self, address: str, symbol: str, decimals: int, name: str | None = None) -> StockToken:
        address = address.lower()
        token = await self.get_token(address)
        if token is not None:
            return token
        token = StockToken(token_address=address, symbol=symbol, decimals=decimals, name=name)
        self.session.add(token)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            token = await self.get_token(address)
            if token is None:
                raise
        else:
            await self.session.refresh(token)
        return token

    async def get_round_by_number(self, round_number: int) -> Round | None:
        result = await self.session.execute(select(Round).where(Round.round_number == round_number))
        return result.scalar_one_or_none()

    async def get_player(self, address: str) -> Player | None:
        result = await self.session.execute(select(Player).where(func.lower(Player.wallet_address) == address.lower()))
        return result.scalar_one_or_none()

    async def upsert_round_stock(self, round_id: UUID, token_id: UUID, amount: int, tx_hash: str | None) -> RoundStock:
        result = await self.session.execute(select(RoundStock).where(RoundStock.round_id == round_id, RoundStock.stock_token_id == token_id))
        item = result.scalar_one_or_none()
        if item is None:
            item = RoundStock(round_id=round_id, stock_token_id=token_id, amount_received=Decimal(amount), purchase_tx_hash=tx_hash, status="RECEIVED")
            self.session.add(item)
        else:
            item.amount_received = Decimal(amount)
            item.purchase_tx_hash = tx_hash or item.purchase_tx_hash
            item.status = "RECEIVED"
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def upsert_reward(self, *, round_id: UUID, player_id: UUID, token_id: UUID, contribution: int, total_contribution: int, entitlement: int, claimed: int) -> StockReward:
        result = await self.session.execute(select(StockReward).where(StockReward.round_id == round_id, StockReward.player_id == player_id, StockReward.stock_token_id == token_id))
        reward = result.scalar_one_or_none()
        claimable = max(0, entitlement - claimed)
        status = "CLAIMED" if entitlement > 0 and claimable == 0 else "AVAILABLE" if claimable > 0 else "PENDING"
        if reward is None:
            reward = StockReward(round_id=round_id, player_id=player_id, stock_token_id=token_id)
            self.session.add(reward)
        reward.contribution = Decimal(contribution)
        reward.total_contribution = Decimal(total_contribution)
        reward.entitlement = Decimal(entitlement)
        reward.claimed_amount = Decimal(claimed)
        reward.claimable_amount = Decimal(claimable)
        reward.claim_status = status
        if status == "CLAIMED" and reward.claimed_at is None:
            reward.claimed_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(reward)
        return reward

    async def record_claim(self, *, round_id: UUID, player_id: UUID, token_id: UUID, amount: int, tx_hash: str) -> bool:
        """Returns False for an already-indexed transaction, making event replay safe."""
        exists = await self.session.execute(select(StockClaim.id).where(StockClaim.transaction_hash == tx_hash.lower()))
        if exists.scalar_one_or_none() is not None:
            return False
        self.session.add(StockClaim(round_id=round_id, player_id=player_id, stock_token_id=token_id, amount=Decimal(amount), transaction_hash=tx_hash.lower()))
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            return False
        return True

    async def rewards_for_wallet(self, wallet_address: str) -> list[tuple[StockReward, Round, StockToken]]:
        result = await self.session.execute(
            select(StockReward, Round, StockToken)
            .join(Player, StockReward.player_id == Player.id)
            .join(Round, StockReward.round_id == Round.id)
            .join(StockToken, StockReward.stock_token_id == StockToken.id)
            .where(func.lower(Player.wallet_address) == wallet_address.lower())
            .order_by(Round.round_number.desc())
        )
        return list(result.all())

    async def stocks_for_round(self, round_id: UUID) -> list[tuple[RoundStock, StockToken]]:
        result = await self.session.execute(
            select(RoundStock, StockToken)
            .join(StockToken, RoundStock.stock_token_id == StockToken.id)
            .where(RoundStock.round_id == round_id)
        )
        return list(result.all())
