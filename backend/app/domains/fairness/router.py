from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_fairness_service
from app.domains.fairness.schema import FairnessRoundResponse, FairnessVerifyRequest, FairnessVerifyResponse
from app.domains.fairness.service import FairnessService

router = APIRouter(prefix="/api/v1/fairness", tags=["fairness"])


@router.get("/rounds/{round_id}", response_model=FairnessRoundResponse)
async def get_round_fairness(round_id: str, service: FairnessService = Depends(get_fairness_service)) -> FairnessRoundResponse:
    try:
        data = await service.get_round(round_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FairnessRoundResponse.model_validate(data)


@router.post("/verify", response_model=FairnessVerifyResponse)
async def verify_round(payload: FairnessVerifyRequest, service: FairnessService = Depends(get_fairness_service)) -> FairnessVerifyResponse:
    try:
        return await service.verify(payload.round_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
