from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TreasuryRead(BaseModel):
    id: UUID
    treasury_balance: int
    reserved_balance: int
    available_balance: int
    updated_at: datetime
