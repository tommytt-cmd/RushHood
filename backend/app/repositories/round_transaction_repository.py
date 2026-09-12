from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.round_transaction import RoundTransaction


class RoundTransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        round_id: UUID,
        round_number: int,
        type: str,
        transaction_hash: str,
    ) -> RoundTransaction:
        round_transaction = RoundTransaction(
            round_id=round_id,
            round_number=round_number,
            type=type,
            transaction_hash=transaction_hash,
        )
        self.session.add(round_transaction)
        await self.session.commit()
        await self.session.refresh(round_transaction)
        return round_transaction

    async def get_by_round_and_type(self, round_id: UUID, type: str) -> RoundTransaction | None:
        result = await self.session.execute(
            select(RoundTransaction).where(
                RoundTransaction.round_id == round_id,
                RoundTransaction.type == type,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_transaction_hash(self, transaction_hash: str) -> RoundTransaction | None:
        result = await self.session.execute(
            select(RoundTransaction).where(RoundTransaction.transaction_hash == transaction_hash)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        transaction: RoundTransaction,
        status: str,
        error_message: str | None = None,
        transaction_hash: str | None = None,
    ) -> RoundTransaction:
        transaction.status = status
        if transaction_hash is not None:
            transaction.transaction_hash = transaction_hash
        transaction.error_message = error_message
        transaction.updated_at = datetime.now(timezone.utc)
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction
