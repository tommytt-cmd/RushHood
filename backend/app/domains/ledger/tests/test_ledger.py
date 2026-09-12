from __future__ import annotations

import pytest
from datetime import datetime, timezone
from uuid import UUID

from app.domains.ledger.model import LedgerEntry, LedgerEntryType, LedgerStatus
from app.domains.ledger.repository import LedgerRepository


@pytest.mark.asyncio
async def test_create_ledger_entry(session):
    repository = LedgerRepository(session)
    entry = LedgerEntry(
        wallet_id=UUID(int=1),
        round_id=UUID(int=2),
        entry_type=LedgerEntryType.BET,
        amount=100,
        asset="ETH",
        status=LedgerStatus.PENDING,
        reference_id="ref-1",
    )
    created = await repository.create(entry)

    assert created.id is not None
    assert created.wallet_id == entry.wallet_id
    assert created.round_id == entry.round_id
    assert created.entry_type == LedgerEntryType.BET
    assert created.amount == 100
    assert created.status == LedgerStatus.PENDING
    assert created.reference_id == "ref-1"
    assert created.created_at.tzinfo is not None


@pytest.mark.asyncio
async def test_ledger_immutable(session):
    repository = LedgerRepository(session)
    entry = LedgerEntry(
        wallet_id=UUID(int=3),
        round_id=UUID(int=4),
        entry_type=LedgerEntryType.PAYOUT,
        amount=250,
        asset="ETH",
    )
    created = await repository.create(entry)

    created.amount = 1000
    with pytest.raises(Exception):
        await repository.create(created)
