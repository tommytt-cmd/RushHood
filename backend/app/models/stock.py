from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StockIndexerCheckpoint(Base):
    """Durable progress marker for the StockVault event indexer."""

    __tablename__ = "stock_indexer_checkpoints"

    # The vault address identifies an independent event stream.  This permits
    # a new vault to be indexed without overwriting the previous vault's
    # progress marker.
    vault_address: Mapped[str] = mapped_column(String(42), primary_key=True)
    last_indexed_block: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False
    )


class StockToken(Base):
    __tablename__ = "stock_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    token_address: Mapped[str] = mapped_column(String(42), unique=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decimals: Mapped[int] = mapped_column(Integer, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


class RoundStock(Base):
    __tablename__ = "round_stocks"
    __table_args__ = (
        UniqueConstraint("round_id", "stock_token_id", name="uq_round_stock_round_token"),
        Index("ix_round_stocks_round_id", "round_id"),
        Index("ix_round_stocks_stock_token_id", "stock_token_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    round_id: Mapped[UUID] = mapped_column(ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False)
    stock_token_id: Mapped[UUID] = mapped_column(ForeignKey("stock_tokens.id"), nullable=False)
    eth_spent: Mapped[Decimal | None] = mapped_column(Numeric(78, 0), nullable=True)
    amount_received: Mapped[Decimal] = mapped_column(Numeric(78, 0), nullable=False, default=0)
    purchase_tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


class StockReward(Base):
    __tablename__ = "stock_rewards"
    __table_args__ = (
        UniqueConstraint("round_id", "player_id", "stock_token_id", name="uq_stock_reward_round_player_token"),
        Index("ix_stock_rewards_player_id", "player_id"),
        Index("ix_stock_rewards_round_id", "round_id"),
        Index("ix_stock_rewards_stock_token_id", "stock_token_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    round_id: Mapped[UUID] = mapped_column(ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    stock_token_id: Mapped[UUID] = mapped_column(ForeignKey("stock_tokens.id"), nullable=False)
    contribution: Mapped[Decimal] = mapped_column(Numeric(78, 0), nullable=False, default=0)
    total_contribution: Mapped[Decimal] = mapped_column(Numeric(78, 0), nullable=False, default=0)
    entitlement: Mapped[Decimal] = mapped_column(Numeric(78, 0), nullable=False, default=0)
    claimed_amount: Mapped[Decimal] = mapped_column(Numeric(78, 0), nullable=False, default=0)
    claimable_amount: Mapped[Decimal] = mapped_column(Numeric(78, 0), nullable=False, default=0)
    claim_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    last_claim_tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


class StockClaim(Base):
    __tablename__ = "stock_claims"
    __table_args__ = (
        Index("ix_stock_claims_player_id", "player_id"),
        Index("ix_stock_claims_round_id", "round_id"),
        Index("ix_stock_claims_transaction_hash", "transaction_hash"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    round_id: Mapped[UUID] = mapped_column(ForeignKey("rounds.id"), nullable=False)
    player_id: Mapped[UUID] = mapped_column(ForeignKey("players.id"), nullable=False)
    stock_token_id: Mapped[UUID] = mapped_column(ForeignKey("stock_tokens.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(78, 0), nullable=False)
    transaction_hash: Mapped[str] = mapped_column(String(66), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="CONFIRMED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
