from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_profile_service
from app.schemas.profile import (
    ProfileAchievement,
    ProfileHistoryItem,
    ProfileStatPoint,
    ProfileSummary,
)
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


def _validate_wallet_address(wallet_address: str) -> str:
    if not wallet_address or not wallet_address.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="wallet_address is required")
    return wallet_address.strip().lower()


@router.get("", response_model=ProfileSummary)
async def get_profile(
    wallet_address: str = Query(..., description="Wallet address for profile data"),
    profile_service: ProfileService = Depends(get_profile_service),
) -> ProfileSummary:
    wallet_address = _validate_wallet_address(wallet_address)
    return await profile_service.get_profile(wallet_address)


@router.get("/stats", response_model=list[ProfileStatPoint])
async def get_profile_stats(
    wallet_address: str = Query(..., description="Wallet address for profile stats"),
    profile_service: ProfileService = Depends(get_profile_service),
) -> list[ProfileStatPoint]:
    wallet_address = _validate_wallet_address(wallet_address)
    return await profile_service.get_stats(wallet_address)


@router.get("/history", response_model=list[ProfileHistoryItem])
async def get_profile_history(
    wallet_address: str = Query(..., description="Wallet address for profile history"),
    profile_service: ProfileService = Depends(get_profile_service),
) -> list[ProfileHistoryItem]:
    wallet_address = _validate_wallet_address(wallet_address)
    return await profile_service.get_history(wallet_address)


@router.get("/achievements", response_model=list[ProfileAchievement])
async def get_profile_achievements(
    wallet_address: str = Query(..., description="Wallet address for profile achievements"),
    profile_service: ProfileService = Depends(get_profile_service),
) -> list[ProfileAchievement]:
    wallet_address = _validate_wallet_address(wallet_address)
    return await profile_service.get_achievements(wallet_address)
