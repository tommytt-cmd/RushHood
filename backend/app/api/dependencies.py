from collections.abc import AsyncGenerator

from fastapi import Depends, Request, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.domains.fairness.service import FairnessService
from app.domains.security.audit import AuditRepository
from app.domains.security.commitment import RoundCommitment
from app.domains.security.replay import ReplayProtectionService
from app.domains.security.seed_manager import SeedManager, ServerSeedRepository


class RoundCommitmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_round_id(self, round_id: str):
        return None
from app.domains.security.verifier import CommitmentVerifier
from app.repositories.bet_repository import BetRepository
from app.repositories.player_repository import PlayerRepository
from app.repositories.round_repository import RoundRepository
from app.repositories.video_repository import VideoRepository
from app.repositories.wallet_repository import WalletRepository, WalletSessionRepository
from app.repositories.player_settlement_repository import PlayerSettlementRepository
from app.repositories.stock_repository import StockRepository
from app.services.bet_service import BetService
from app.services.round_service import RoundService
from app.services.player_settlement_service import PlayerSettlementService
from app.services.settlement_service import SettlementService
from app.services.wallet_service import WalletService
from app.video.service import VideoService


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


async def get_round_repository(session: AsyncSession = Depends(get_session)) -> RoundRepository:
    return RoundRepository(session)


async def get_player_repository(session: AsyncSession = Depends(get_session)) -> PlayerRepository:
    return PlayerRepository(session)


async def get_bet_repository(session: AsyncSession = Depends(get_session)) -> BetRepository:
    return BetRepository(session)


async def get_video_repository(session: AsyncSession = Depends(get_session)) -> VideoRepository:
    return VideoRepository(session)


async def get_round_service(
    round_repository: RoundRepository = Depends(get_round_repository),
    video_repository: VideoRepository = Depends(get_video_repository),
) -> RoundService:
    return RoundService(round_repository, video_repository)


async def get_video_service(session: AsyncSession = Depends(get_session)) -> VideoService:
    return VideoService(session)


async def get_profile_service(
    player_repository: PlayerRepository = Depends(get_player_repository),
    bet_repository: BetRepository = Depends(get_bet_repository),
    round_repository: RoundRepository = Depends(get_round_repository),
    video_repository: VideoRepository = Depends(get_video_repository),
    session: AsyncSession = Depends(get_session),
) -> "ProfileService":
    from app.services.profile_service import ProfileService

    return ProfileService(player_repository, bet_repository, round_repository, video_repository, StockRepository(session))


def get_replay_service(websocket: WebSocket):
    return getattr(websocket.app.state, "replay_service", None)


async def get_bet_service(
    round_repository: RoundRepository = Depends(get_round_repository),
    player_repository: PlayerRepository = Depends(get_player_repository),
    bet_repository: BetRepository = Depends(get_bet_repository),
) -> BetService:
    return BetService(round_repository, player_repository, bet_repository)


async def get_settlement_service(
    round_repository: RoundRepository = Depends(get_round_repository),
    bet_repository: BetRepository = Depends(get_bet_repository),
) -> SettlementService:
    return SettlementService(round_repository, bet_repository)


async def get_player_settlement_service(
    request: Request,
    round_repository: RoundRepository = Depends(get_round_repository),
    player_repository: PlayerRepository = Depends(get_player_repository),
    bet_repository: BetRepository = Depends(get_bet_repository),
    session: AsyncSession = Depends(get_session),
) -> PlayerSettlementService:
    publisher = getattr(request.app.state, "publisher", None)
    oracle_client = getattr(request.app.state, "oracle_client", None)
    player_settlement_repository = PlayerSettlementRepository(session)
    return PlayerSettlementService(
        round_repository,
        player_repository,
        bet_repository,
        player_settlement_repository,
        oracle_client=oracle_client,
        publisher=publisher,
    )


async def get_wallet_repository(session: AsyncSession = Depends(get_session)) -> WalletRepository:
    return WalletRepository(session)


async def get_wallet_session_repository(session: AsyncSession = Depends(get_session)) -> WalletSessionRepository:
    return WalletSessionRepository(session)


async def get_wallet_service(
    wallet_repository: WalletRepository = Depends(get_wallet_repository),
    wallet_session_repository: WalletSessionRepository = Depends(get_wallet_session_repository),
) -> WalletService:
    return WalletService(wallet_repository, wallet_session_repository)


async def get_seed_repository(session: AsyncSession = Depends(get_session)) -> ServerSeedRepository:
    return ServerSeedRepository(session)


async def get_audit_repository(session: AsyncSession = Depends(get_session)) -> AuditRepository:
    return AuditRepository(session)


async def get_commitment_repository(session: AsyncSession = Depends(get_session)) -> RoundCommitmentRepository:
    return RoundCommitmentRepository(session)


async def get_seed_manager(seed_repository: ServerSeedRepository = Depends(get_seed_repository)) -> SeedManager:
    return SeedManager(seed_repository)


async def get_commitment_verifier(
    round_repository: RoundRepository = Depends(get_round_repository),
    seed_manager: SeedManager = Depends(get_seed_manager),
    commitment_repository: RoundCommitmentRepository = Depends(get_commitment_repository),
) -> CommitmentVerifier:
    return CommitmentVerifier(round_repository, seed_manager, commitment_repository)


async def get_fairness_service(
    round_repository: RoundRepository = Depends(get_round_repository),
    verifier: CommitmentVerifier = Depends(get_commitment_verifier),
    commitment_repository: RoundCommitmentRepository = Depends(get_commitment_repository),
) -> FairnessService:
    return FairnessService(round_repository, verifier, commitment_repository)


async def get_replay_protection_service() -> ReplayProtectionService:
    return ReplayProtectionService()
