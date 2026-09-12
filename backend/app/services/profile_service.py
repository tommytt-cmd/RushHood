from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Iterable

from app.core.enums import BetStatus
from app.models.bet import Bet
from app.repositories.bet_repository import BetRepository
from app.repositories.player_repository import PlayerRepository
from app.repositories.round_repository import RoundRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.profile import (
    ProfileAchievement,
    ProfileHistoryItem,
    ProfileStatPoint,
    ProfileSummary,
    StockRewardRoundResponse,
    StockRewardTokenResponse,
    WalletProfileResponse,
)
from app.repositories.stock_repository import StockRepository
from app.models.wallet import Wallet


class ProfileService:
    def __init__(
        self,
        player_repository: PlayerRepository,
        bet_repository: BetRepository,
        round_repository: RoundRepository,
        video_repository: VideoRepository,
        stock_repository: StockRepository | None = None,
    ) -> None:
        self.player_repository = player_repository
        self.bet_repository = bet_repository
        self.round_repository = round_repository
        self.video_repository = video_repository
        self.stock_repository = stock_repository

    async def get_authenticated_wallet_profile(self, wallet: Wallet) -> WalletProfileResponse:
        """Return cached indexed data for the authenticated session only.

        Amounts remain decimal strings so this API never loses uint256 precision.
        ``Round.round_number`` is deliberately the StockVault ``roundId`` mapping.
        """
        summary = await self.get_profile(wallet.wallet_address)
        history = await self.get_history(wallet.wallet_address, limit=25)
        rows = await self.stock_repository.rewards_for_wallet(wallet.wallet_address) if self.stock_repository else []
        grouped: dict[object, StockRewardRoundResponse] = {}
        for reward, round_model, token in rows:
            key = round_model.id
            if key not in grouped:
                grouped[key] = StockRewardRoundResponse(
                    round_id=str(round_model.id),
                    round_number=int(round_model.round_number),
                    result="WON",
                    contribution=str(reward.contribution),
                    stocks=[],
                )
            grouped[key].stocks.append(StockRewardTokenResponse(
                token=token.token_address,
                symbol=token.symbol,
                name=token.name,
                decimals=token.decimals,
                entitlement=str(reward.entitlement),
                claimed=str(reward.claimed_amount),
                claimable=str(reward.claimable_amount),
                claim_status=reward.claim_status,
            ))
        return WalletProfileResponse(
            wallet={"address": wallet.wallet_address, "chainId": wallet.chain_id},
            stats={"totalBets": summary.total_bets, "wins": summary.total_wins, "losses": summary.total_losses, "winRate": summary.win_rate, "totalWagered": str(summary.total_staked)},
            stock_rewards=list(grouped.values()),
            recent_bets=history,
        )

    async def get_profile(self, wallet_address: str) -> ProfileSummary:
        normalized = wallet_address.lower()
        player = await self.player_repository.get_by_wallet(normalized)
        bets = await self.bet_repository.list_by_player(normalized)
        rounds = await self._load_rounds(bets)
        videos = await self._load_videos(rounds.values())

        total_bets = len(bets)
        total_staked = sum(bet.stake for bet in bets)
        total_wins = sum(1 for bet in bets if bet.status == BetStatus.WON)
        total_losses = sum(1 for bet in bets if bet.status == BetStatus.LOST)
        win_rate = (total_wins / total_bets * 100) if total_bets > 0 else 0.0
        last_active_at = max((bet.created_at for bet in bets), default=None)
        current_streak = self._current_win_streak(bets)
        favorite_location = self._favorite_location(rounds, videos)

        return ProfileSummary(
            wallet_address=normalized,
            joined_at=player.created_at if player is not None else None,
            total_bets=total_bets,
            total_staked=total_staked,
            total_wins=total_wins,
            total_losses=total_losses,
            win_rate=round(win_rate, 1),
            current_streak=current_streak,
            last_active_at=last_active_at,
            favorite_location=favorite_location,
        )

    async def get_stats(self, wallet_address: str, limit: int = 10) -> list[ProfileStatPoint]:
        normalized = wallet_address.lower()
        bets = await self.bet_repository.list_by_player(normalized)
        bets = sorted(bets, key=lambda bet: bet.created_at, reverse=True)[:limit]
        rounds = await self._load_rounds(bets)

        points: list[ProfileStatPoint] = []
        for bet in reversed(bets):
            round_model = rounds.get(bet.round_id)
            label = f"Round {round_model.round_number}" if round_model and round_model.round_number is not None else "Recent"
            points.append(
                ProfileStatPoint(
                    label=label,
                    bets=1,
                    wins=1 if bet.status == BetStatus.WON else 0,
                    losses=1 if bet.status == BetStatus.LOST else 0,
                    stake=bet.stake,
                    profit=self._profit_for_bet(bet),
                ),
            )

        return points

    async def get_history(self, wallet_address: str, limit: int = 12) -> list[ProfileHistoryItem]:
        normalized = wallet_address.lower()
        bets = await self.bet_repository.list_by_player(normalized)
        bets = sorted(bets, key=lambda bet: bet.created_at, reverse=True)[:limit]
        rounds = await self._load_rounds(bets)

        return [
            ProfileHistoryItem(
                bet_id=bet.id,
                round_id=bet.round_id,
                round_number=rounds.get(bet.round_id).round_number if rounds.get(bet.round_id) else None,
                prediction=bet.prediction,
                result=rounds.get(bet.round_id).result if rounds.get(bet.round_id) else None,
                status=bet.status,
                stake=bet.stake,
                created_at=bet.created_at,
            )
            for bet in bets
        ]

    async def get_achievements(self, wallet_address: str) -> list[ProfileAchievement]:
        normalized = wallet_address.lower()
        profile = await self.get_profile(normalized)

        achievements: list[ProfileAchievement] = [
            ProfileAchievement(
                id="first-bet",
                title="First bet",
                description="Place your first stake on a traffic round.",
                progress=min(profile.total_bets, 1),
                goal=1,
                unlocked=profile.total_bets >= 1,
            ),
            ProfileAchievement(
                id="risk-taker",
                title="Risk taker",
                description="Place 10 bets across live rounds.",
                progress=min(profile.total_bets, 10),
                goal=10,
                unlocked=profile.total_bets >= 10,
            ),
            ProfileAchievement(
                id="hot-streak",
                title="Hot streak",
                description="Win three rounds in a row.",
                progress=min(profile.current_streak, 3),
                goal=3,
                unlocked=profile.current_streak >= 3,
            ),
            ProfileAchievement(
                id="veteran-player",
                title="Veteran player",
                description="Build a book of 25 market positions.",
                progress=min(profile.total_bets, 25),
                goal=25,
                unlocked=profile.total_bets >= 25,
            ),
        ]

        return achievements

    async def _load_rounds(self, bets: Iterable[Bet]) -> dict[object, object]:
        round_ids = {bet.round_id for bet in bets}
        if not round_ids:
            return {}

        rounds = await self.round_repository.list_by_ids(round_ids)
        return {round_model.id: round_model for round_model in rounds}

    async def _load_videos(self, rounds: Iterable[object]) -> dict[object, object]:
        video_ids = {round_model.video_id for round_model in rounds if round_model and round_model.video_id is not None}
        if not video_ids:
            return {}

        videos = await self.video_repository.list_by_ids(video_ids)
        return {video.id: video for video in videos}

    def _current_win_streak(self, bets: Iterable[Bet]) -> int:
        streak = 0
        for bet in sorted(bets, key=lambda bet: bet.created_at, reverse=True):
            if bet.status == BetStatus.WON:
                streak += 1
                continue
            break
        return streak

    def _profit_for_bet(self, bet: Bet) -> int:
        if bet.status == BetStatus.WON:
            return bet.stake
        if bet.status == BetStatus.LOST:
            return -bet.stake
        return 0

    def _favorite_location(self, rounds: dict[object, object], videos: dict[object, object]) -> str | None:
        location_counts: Counter[str] = Counter()
        for round_model in rounds.values():
            if round_model.video_id is None:
                continue
            video = videos.get(round_model.video_id)
            if not video or not getattr(video, "location_name", None):
                continue
            location_counts[video.location_name] += 1

        if not location_counts:
            return None

        return location_counts.most_common(1)[0][0]
