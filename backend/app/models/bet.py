from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import BetStatus
from app.database.base import Base


class Bet(Base):
    __tablename__ = "bets"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    round_id: Mapped[UUID] = mapped_column(ForeignKey("rounds.id"), nullable=False)
    player_id: Mapped[UUID] = mapped_column(ForeignKey("players.id"), nullable=False)
    prediction: Mapped[int] = mapped_column(default=0)
    # On-chain amounts are wei values; an INTEGER/INT4 column overflows above
    # roughly 2.1 billion wei. Use PostgreSQL BIGINT for persisted stakes.
    stake: Mapped[int] = mapped_column(BigInteger, default=0)
    # The mined wallet transaction is the idempotency key for on-chain sync.
    transaction_hash: Mapped[str | None] = mapped_column(String(66), unique=True, nullable=True)
    onchain_round_number: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[BetStatus] = mapped_column(default=BetStatus.PENDING)
    # Keep this aligned with the existing TIMESTAMP WITHOUT TIME ZONE column.
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
