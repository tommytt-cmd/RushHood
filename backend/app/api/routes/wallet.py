from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Header, status

from app.api.dependencies import get_wallet_service
from app.services.wallet_service import WalletService
from app.services.profile_service import ProfileService
from app.api.dependencies import get_profile_service
from app.schemas.profile import WalletProfileResponse

router = APIRouter(prefix="/api/v1/wallet", tags=["wallet"])


class ChallengeRequest(BaseModel):
    wallet_address: str = Field(..., description="Wallet address")
    chain_id: int = Field(..., description="Blockchain chain ID")


class LoginRequest(BaseModel):
    wallet_address: str = Field(..., description="Wallet address")
    chain_id: int = Field(..., description="Blockchain chain ID")
    signature: str = Field(..., description="Signed message")
    nonce: str = Field(..., description="Nonce that was signed")


@router.post("/challenge", tags=["wallet-authentication"])
async def request_challenge(
    request: ChallengeRequest,
    wallet_service: WalletService = Depends(get_wallet_service),
) -> dict:
    """
    Request a challenge (nonce) to sign for wallet authentication.

    Args:
        request: ChallengeRequest with wallet_address and chain_id

    Returns:
        Challenge response with nonce and expiration time
    """
    try:
        challenge = await wallet_service.request_challenge(
            request.wallet_address,
            request.chain_id,
        )
        return {
            "success": True,
            "data": challenge,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request challenge",
        )


@router.post("/login", tags=["wallet-authentication"])
async def login(
    request: LoginRequest,
    wallet_service: WalletService = Depends(get_wallet_service),
) -> dict:
    """
    Login by submitting a signed nonce.

    Args:
        request: LoginRequest with wallet_address, chain_id, signature, and nonce

    Returns:
        Login response with session_token and wallet profile
    """
    try:
        result = await wallet_service.login(
            request.wallet_address,
            request.chain_id,
            request.signature,
            request.nonce,
        )
        return {
            "success": True,
            "data": result,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to login",
        )


@router.post("/logout", tags=["wallet-authentication"])
async def logout(
    authorization: str | None = Header(None),
    wallet_service: WalletService = Depends(get_wallet_service),
) -> dict:
    """
    Logout by revoking the session token.

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        Success response
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    session_token = authorization[7:]  # Remove "Bearer " prefix
    await wallet_service.logout(session_token)
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", tags=["wallet-authentication"])
async def get_profile(
    authorization: str | None = Header(None),
    wallet_service: WalletService = Depends(get_wallet_service),
) -> dict:
    """
    Get the authenticated wallet profile.

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        Wallet profile if authenticated
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    session_token = authorization[7:]  # Remove "Bearer " prefix
    wallet = await wallet_service.get_authenticated_wallet(session_token)

    if wallet is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
        )

    return {
        "success": True,
        "data": {
            "id": str(wallet.id),
            "wallet_address": wallet.wallet_address,
            "chain_id": wallet.chain_id,
            "first_seen_at": wallet.first_seen_at.isoformat(),
            "last_login_at": wallet.last_login_at.isoformat() if wallet.last_login_at else None,
            "created_at": wallet.created_at.isoformat(),
            "updated_at": wallet.updated_at.isoformat(),
        },
    }


@router.get("/me/profile", response_model=WalletProfileResponse, tags=["wallet-authentication"])
async def get_wallet_profile(
    authorization: str | None = Header(None),
    wallet_service: WalletService = Depends(get_wallet_service),
    profile_service: ProfileService = Depends(get_profile_service),
) -> WalletProfileResponse:
    """Profile data is bound to the signed-wallet session, never a query address."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    wallet = await wallet_service.get_authenticated_wallet(authorization[7:])
    if wallet is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session token")
    return await profile_service.get_authenticated_wallet_profile(wallet)
