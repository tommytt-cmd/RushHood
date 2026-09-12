from __future__ import annotations

from uuid import UUID

from app.domains.ledger.model import LedgerEntry, LedgerEntryType, LedgerStatus
from app.domains.ledger.repository import LedgerRepository


class LedgerService:
    def __init__(self, ledger_repository: LedgerRepository) -> None:
        self.ledger_repository = ledger_repository

    async def record_entry(
        self,
        wallet_id: UUID,
        round_id: UUID,
        entry_type: str,
        amount: int,
        asset: str = "ETH",
        status: str = LedgerStatus.PENDING,
        reference_id: str | None = None,
    ) -> LedgerEntry:
        entry = LedgerEntry(
            wallet_id=wallet_id,
            round_id=round_id,
            entry_type=entry_type,
            amount=amount,
            asset=asset,
            status=status,
            reference_id=reference_id,
        )
        return await self.ledger_repository.create(entry)

    async def list_by_wallet(self, wallet_id: UUID) -> list[LedgerEntry]:
        return await self.ledger_repository.list_by_wallet(wallet_id)

    async def list_all(self) -> list[LedgerEntry]:
        return await self.ledger_repository.list_all()

    async def list_by_round(self, round_id: UUID) -> list[LedgerEntry]:
        return await self.ledger_repository.list_by_round(round_id)
