from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, BigInteger, Identity
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import BuybackStatus, FinancialReconciliationStatus, RoundStatus
from app.database.base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Round(Base):
    __tablename__ = "rounds"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    round_number: Mapped[int] = mapped_column(
        BigInteger,
        Identity(start=1, always=False),
        unique=True,
        # PostgreSQL identity columns cannot be emitted as both nullable and
        # generated.  A round number is required once the row is persisted.
        nullable=False,
    )
    video_id: Mapped[UUID | None] = mapped_column(ForeignKey("videos.id"), nullable=True)
    status: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default=RoundStatus.WAITING.value,
    )
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    betting_closes_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    locked_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    live_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    result: Mapped[int | None] = mapped_column(default=None)
    threshold: Mapped[int | None] = mapped_column(BigInteger, nullable=True, default=None)
    settlement_status: Mapped[str] = mapped_column(
        String(255), nullable=False, default="NOT_STARTED"
    )
    settlement_tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    settlement_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    settlement_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    buyback_status: Mapped[str] = mapped_column(
        String(255), nullable=False, default=BuybackStatus.PENDING.value
    )
    buyback_allocation_wei: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    buyback_execution_tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    buyback_finalization_tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    buyback_error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    buyback_attempts: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    buyback_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    reconciliation_status: Mapped[str] = mapped_column(
        String(255), nullable=False, default=FinancialReconciliationStatus.NOT_STARTED.value
    )
    reconciliation_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    reconciliation_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    reconciliation_error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    onchain_total_pool: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    onchain_over_pool: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    onchain_under_pool: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    onchain_winner_pool: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    onchain_loser_pool: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    onchain_treasury_fee: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    onchain_protocol_fee_bps: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    onchain_winning_side: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    onchain_final_vehicle_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    onchain_settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    onchain_is_tie: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    onchain_status: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
