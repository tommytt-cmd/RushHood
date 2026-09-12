from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    wallet_address: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    chain_id: Mapped[int] = mapped_column(Integer, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class WalletSession(Base):
    __tablename__ = "wallet_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    wallet_id: Mapped[UUID] = mapped_column(ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
    nonce: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
