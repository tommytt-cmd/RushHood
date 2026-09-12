from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.enums import RoundStatus


class RoundRead(BaseModel):
    id: UUID
    video_id: UUID | None = None
    status: RoundStatus
    starts_at: datetime | None = None
    betting_closes_at: datetime | None = None
    ends_at: datetime | None = None
    result: int | None = None
    settlement_status: str | None = None
    buyback_status: str | None = None
    buyback_allocation_wei: int | None = None
    buyback_execution_tx_hash: str | None = None
    buyback_finalization_tx_hash: str | None = None
    buyback_error_message: str | None = None
    buyback_attempts: int | None = None
    buyback_confirmed_at: datetime | None = None
    reconciliation_status: str | None = None
    onchain_total_pool: int | None = None
    onchain_over_pool: int | None = None
    onchain_under_pool: int | None = None
    onchain_winner_pool: int | None = None
    onchain_loser_pool: int | None = None
    onchain_treasury_fee: int | None = None
    onchain_protocol_fee_bps: int | None = None
    onchain_winning_side: int | None = None
    onchain_final_vehicle_count: int | None = None
    onchain_settled_at: datetime | None = None
    onchain_status: int | None = None
    created_at: datetime


class RoundCurrentResponse(BaseModel):
    round: RoundRead
    status: RoundStatus
    countdowns: dict[str, int | None]


class BetCreate(BaseModel):
    wallet_address: str = Field(min_length=1)
    prediction: int = Field(ge=0)
    stake: int = Field(ge=1)


class BetSyncCreate(BaseModel):
    txHash: str = Field(min_length=1)
    walletAddress: str = Field(min_length=1)
    roundId: str = Field(min_length=1)
    side: str = Field(pattern="^(OVER|UNDER)$")
    amountEth: str = Field(min_length=1)
