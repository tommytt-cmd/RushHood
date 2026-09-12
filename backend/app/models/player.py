from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    wallet_address: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # The existing PostgreSQL column is TIMESTAMP WITHOUT TIME ZONE.
    # Store UTC as a naive datetime so asyncpg receives the type it expects.
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
