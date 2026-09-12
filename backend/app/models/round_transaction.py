from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RoundTransactionStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class RoundTransactionType(str, Enum):
    OPEN_ROUND = "OPEN_ROUND"
    LOCK_ROUND = "LOCK_ROUND"
    SUBMIT_RESULT = "SUBMIT_RESULT"


class RoundTransaction(Base):
    __tablename__ = "round_transactions"
    __table_args__ = (UniqueConstraint("round_id", "type", name="uq_round_transaction_type"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    round_id: Mapped[UUID] = mapped_column(ForeignKey("rounds.id"), nullable=False)
    round_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    transaction_hash: Mapped[str] = mapped_column(String(66), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=RoundTransactionStatus.PENDING.value)
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
