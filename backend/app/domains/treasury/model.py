from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Treasury(Base):
    __tablename__ = "treasury"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    treasury_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)

    def recalc_available(self) -> None:
        self.available_balance = self.treasury_balance - self.reserved_balance


class TreasuryEvent:
    pass
