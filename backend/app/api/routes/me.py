from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.api.dependencies import get_profile_service, get_wallet_service
from app.schemas.profile import WalletProfileResponse
from app.services.profile_service import ProfileService
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/api/me", tags=["wallet-profile"])


@router.get("/profile", response_model=WalletProfileResponse)
async def get_my_profile(
    authorization: str | None = Header(None),
    wallet_service: WalletService = Depends(get_wallet_service),
    profile_service: ProfileService = Depends(get_profile_service),
) -> WalletProfileResponse:
    """The address comes only from the valid signed-wallet session."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    wallet = await wallet_service.get_authenticated_wallet(authorization[7:])
    if wallet is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session token")
    return await profile_service.get_authenticated_wallet_profile(wallet)
