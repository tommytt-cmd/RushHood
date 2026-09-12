from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ledger.model import LedgerEntry


class LedgerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, ledger_entry: LedgerEntry) -> LedgerEntry:
        if ledger_entry.id is None:
            ledger_entry.id = uuid4()
        else:
            existing = await self.session.get(LedgerEntry, ledger_entry.id)
            if existing is not None:
                raise ValueError("Ledger entries are immutable and cannot be recreated")

        if ledger_entry.created_at is None or ledger_entry.created_at.tzinfo is None:
            ledger_entry.created_at = datetime.now(timezone.utc)

        self.session.add(ledger_entry)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(ledger_entry)

        if ledger_entry.created_at is not None and ledger_entry.created_at.tzinfo is None:
            ledger_entry.created_at = ledger_entry.created_at.replace(tzinfo=timezone.utc)

        return ledger_entry

    async def list_by_wallet(self, wallet_id: UUID) -> list[LedgerEntry]:
        result = await self.session.execute(select(LedgerEntry).where(LedgerEntry.wallet_id == wallet_id).order_by(LedgerEntry.created_at.desc()))
        return list(result.scalars().all())

    async def list_all(self) -> list[LedgerEntry]:
        result = await self.session.execute(select(LedgerEntry).order_by(LedgerEntry.created_at.desc()))
        return list(result.scalars().all())

    async def list_by_round(self, round_id: UUID) -> list[LedgerEntry]:
        result = await self.session.execute(select(LedgerEntry).where(LedgerEntry.round_id == round_id).order_by(LedgerEntry.created_at.desc()))
        return list(result.scalars().all())
