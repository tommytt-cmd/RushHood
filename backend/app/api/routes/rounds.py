from __future__ import annotations

from decimal import Decimal, InvalidOperation
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.oracle.client import OracleConnectionError

from app.api.dependencies import (
    get_bet_service,
    get_player_settlement_service,
    get_round_service,
    get_settlement_service,
)
from app.schemas.bet import BetRead
from app.schemas.player_settlement import PlayerSettlementRead
from app.schemas.round import BetCreate, BetSyncCreate, RoundCurrentResponse, RoundRead
from app.services.bet_service import BetService
from app.services.player_settlement_service import PlayerSettlementService
from app.services.round_service import RoundService
from app.services.settlement_service import SettlementService

router = APIRouter(prefix="", tags=["rounds"])


@router.get("/round/current", response_model=RoundCurrentResponse)
async def get_current_round(
    round_service: RoundService = Depends(get_round_service),
) -> RoundCurrentResponse:
    round_model = await round_service.get_current_round()
    if round_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No round found")
    return RoundCurrentResponse(
        round=RoundRead.model_validate(
                round_model,
                from_attributes=True
            ),
        status=round_model.status,
        countdowns={
            "betting": None,
            "round": None,
        },
    )


@router.post("/bets", response_model=BetRead, status_code=status.HTTP_201_CREATED)
async def place_bet(
    payload: BetCreate,
    bet_service: BetService = Depends(get_bet_service),
) -> BetRead:
    try:
        bet = await bet_service.place_bet(payload.wallet_address, payload.prediction, payload.stake)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return BetRead.model_validate(bet)


@router.post("/api/bets/sync", response_model=BetRead, status_code=status.HTTP_201_CREATED)
async def sync_onchain_bet(
    payload: BetSyncCreate,
    request: Request,
    bet_service: BetService = Depends(get_bet_service),
) -> BetRead:
    """Record a successfully confirmed on-chain bet in the backend database."""
    try:
        amount_in_wei = Decimal(payload.amountEth) * Decimal(10**18)
        if amount_in_wei != amount_in_wei.to_integral_value():
            raise ValueError
        amount_wei = int(amount_in_wei)
    except (InvalidOperation, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amountEth") from exc

    if amount_wei < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bet amount must be greater than zero")

    try:
        round_uuid = UUID(payload.roundId)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid roundId") from exc

    round_model = await bet_service.round_repository.get_by_id(round_uuid)
    if round_model is None or round_model.round_number is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Round not found")

    prediction = 1 if payload.side == "OVER" else 0
    existing_transaction = await bet_service.bet_repository.get_by_transaction_hash(payload.txHash.lower())
    if existing_transaction is not None:
        if (
            existing_transaction.round_id != round_uuid
            or existing_transaction.prediction != prediction
            or existing_transaction.stake != amount_wei
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction hash is already associated with a different bet",
            )
        return BetRead.model_validate(existing_transaction)

    oracle_client = getattr(request.app.state, "oracle_client", None)
    if oracle_client is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="On-chain verification is unavailable")

    try:
        oracle_client.verify_place_bet_transaction(
            payload.txHash,
            wallet_address=payload.walletAddress,
            round_number=int(round_model.round_number),
            side=prediction,
            amount_wei=amount_wei,
        )
        bet = await bet_service.sync_onchain_bet(
            round_id=round_uuid,
            wallet_address=payload.walletAddress,
            prediction=prediction,
            stake=amount_wei,
            transaction_hash=payload.txHash,
        )
    except (ValueError, OracleConnectionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return BetRead.model_validate(bet)


@router.get("/rounds/{round_id}", response_model=RoundRead)
async def get_round(round_id: str, round_service: RoundService = Depends(get_round_service)) -> RoundRead:
    from uuid import UUID

    try:
        round_uuid = UUID(round_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid round id") from exc

    round_model = await round_service.round_repository.get_by_id(round_uuid)
    if round_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Round not found")
    return RoundRead.model_validate(
            round_model,
            from_attributes=True
        )


@router.get("/players/{wallet}/bets", response_model=list[BetRead])
async def get_player_bets(wallet: str, bet_service: BetService = Depends(get_bet_service)) -> list[BetRead]:
    bets = await bet_service.get_player_bets(wallet)
    return [BetRead.model_validate(bet) for bet in bets]


@router.get("/rounds/{round_id}/players/{wallet}/settlement", response_model=PlayerSettlementRead)
async def get_player_settlement(
    round_id: str,
    wallet: str,
    player_settlement_service: PlayerSettlementService = Depends(get_player_settlement_service),
) -> PlayerSettlementRead:
    from uuid import UUID

    try:
        round_uuid = UUID(round_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid round id") from exc

    try:
        settlement = await player_settlement_service.get_player_settlement(round_uuid, wallet)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return PlayerSettlementRead.model_validate(settlement, from_attributes=True)


@router.post("/rounds/{round_id}/settle")
async def settle_round(
    round_id: str,
    settlement_service: SettlementService = Depends(get_settlement_service),
) -> dict[str, str]:
    from uuid import UUID

    try:
        round_uuid = UUID(round_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid round id") from exc

    try:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Winner side is required for bet settlement; use the scheduler settlement flow.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"status": "settled"}
