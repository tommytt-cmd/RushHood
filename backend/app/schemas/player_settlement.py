from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import BetStatus


class PlayerSettlementRead(BaseModel):
    id: UUID
    round_id: UUID
    player_id: UUID | None = None
    wallet_address: str
    bet_prediction: int | None = None
    bet_stake: int | None = None
    bet_status: BetStatus | None = None
    over_amount: int | None = None
    under_amount: int | None = None
    is_winner: bool | None = None
    claim_status: str | None = None
    claimable_eth: int | None = None
    claimable_reward: int | None = None
    pending_eth: int | None = None
    rush_claimed: bool | None = None
    has_claimed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }
