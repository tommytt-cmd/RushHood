from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class LedgerEntryType(str):
    BET = "BET"
    HOUSE_FEE = "HOUSE_FEE"
    PAYOUT = "PAYOUT"
    REFUND = "REFUND"
    TREASURY_DEPOSIT = "TREASURY_DEPOSIT"
    TREASURY_WITHDRAWAL = "TREASURY_WITHDRAWAL"


class LedgerStatus(str):
    PENDING = "PENDING"
    SETTLED = "SETTLED"
    FAILED = "FAILED"


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    wallet_id: Mapped[UUID] = mapped_column(ForeignKey("wallets.id"), nullable=False)
    round_id: Mapped[UUID] = mapped_column(ForeignKey("rounds.id"), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    asset: Mapped[str] = mapped_column(String(50), default="ETH", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=LedgerStatus.PENDING, nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
