from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PlayerSettlement(Base):
    __tablename__ = "player_settlements"
    __table_args__ = (
        UniqueConstraint("round_id", "wallet_address", name="uq_player_settlements_round_wallet"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    round_id: Mapped[UUID] = mapped_column(ForeignKey("rounds.id"), nullable=False)
    player_id: Mapped[UUID | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    wallet_address: Mapped[str] = mapped_column(String(255), nullable=False)
    bet_prediction: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    bet_stake: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    bet_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    over_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    under_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_winner: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    claim_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    claimable_eth: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    claimable_reward: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    pending_eth: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    rush_claimed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_claimed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
