from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import BetStatus


class BetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    round_id: UUID
    player_id: UUID
    prediction: int
    stake: int
    status: BetStatus
    created_at: datetime


class BetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    round_id: UUID
    player_id: UUID
    prediction: int
    stake: int
    status: BetStatus
    created_at: datetime
