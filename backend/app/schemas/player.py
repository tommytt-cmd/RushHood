from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PlayerCreate(BaseModel):
    wallet_address: str = Field(min_length=1)


class PlayerRead(BaseModel):
    id: UUID
    wallet_address: str
    created_at: datetime
