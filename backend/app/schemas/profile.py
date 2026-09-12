from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import BetStatus


class ProfileSummary(BaseModel):
    wallet_address: str
    joined_at: datetime | None = None
    total_bets: int
    total_staked: int
    total_wins: int
    total_losses: int
    win_rate: float
    current_streak: int
    last_active_at: datetime | None = None
    favorite_location: str | None = None


class ProfileStatPoint(BaseModel):
    label: str
    bets: int
    wins: int
    losses: int
    stake: int
    profit: int


class ProfileHistoryItem(BaseModel):
    bet_id: UUID
    round_id: UUID
    round_number: int | None = None
    prediction: int
    result: int | None = None
    status: BetStatus
    stake: int
    created_at: datetime


class ProfileAchievement(BaseModel):
    id: str
    title: str
    description: str
    progress: int
    goal: int
    unlocked: bool


class StockRewardTokenResponse(BaseModel):
    token: str
    symbol: str
    name: str | None = None
    decimals: int
    entitlement: str
    claimed: str
    claimable: str
    claim_status: str


class StockRewardRoundResponse(BaseModel):
    round_id: str
    round_number: int
    result: str
    prediction: int | None = None
    contribution: str
    stocks: list[StockRewardTokenResponse]


class WalletProfileResponse(BaseModel):
    wallet: dict[str, object]
    stats: dict[str, object]
    stock_rewards: list[StockRewardRoundResponse]
    recent_bets: list[ProfileHistoryItem]
