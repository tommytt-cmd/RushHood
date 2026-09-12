from __future__ import annotations

import logging

from app.core.enums import BetStatus
from app.models.bet import Bet
from app.repositories.bet_repository import BetRepository
from app.repositories.round_repository import RoundRepository

logger = logging.getLogger("game")


class SettlementService:
    def __init__(self, round_repository: RoundRepository, bet_repository: BetRepository) -> None:
        self.round_repository = round_repository
        self.bet_repository = bet_repository

    async def settle_round(self, round_id, winner_side: int | None = None) -> list[Bet]:
        round_model = await self.round_repository.get_by_id(round_id)
        if round_model is None:
            raise ValueError("Round not found")
        if round_model.result is None:
            raise ValueError("Round result not available")

        if winner_side is None:
            raise ValueError("Winner side is required to settle bets")

        bets = await self.bet_repository.list_by_round(round_id)
        for bet in bets:
            bet.status = BetStatus.WON if bet.prediction == winner_side else BetStatus.LOST
            await self.bet_repository.update(bet)

        logger.info("settlement_completed", extra={"round_id": str(round_id), "result": round_model.result})
        return bets
