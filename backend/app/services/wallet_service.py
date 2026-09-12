from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.models.wallet import Wallet
from app.repositories.wallet_repository import WalletRepository, WalletSessionRepository
from app.services.signature_verifier import SignatureVerifier

logger = logging.getLogger("wallet")

# Configuration constants
NONCE_EXPIRATION_MINUTES = 15
SESSION_EXPIRATION_HOURS = 24
SUPPORTED_CHAINS = {
    1: "Ethereum Mainnet",
    11155111: "Ethereum Sepolia",
    8453: "Base",
    84532: "Base Sepolia",
    31337: "Local Hardhat",
}


class WalletService:
    def __init__(
        self,
        wallet_repository: WalletRepository,
        wallet_session_repository: WalletSessionRepository,
    ) -> None:
        self.wallet_repository = wallet_repository
        self.wallet_session_repository = wallet_session_repository
        self.verifier = SignatureVerifier()

    async def request_challenge(self, wallet_address: str, chain_id: int) -> dict[str, str | int]:
        """
        Generate a challenge (nonce) for the wallet to sign.

        Args:
            wallet_address: The wallet address requesting a challenge
            chain_id: The blockchain chain ID

        Returns:
            Dict with nonce and expiration time
        """
        # Validate chain
        if chain_id not in SUPPORTED_CHAINS:
            raise ValueError(f"Unsupported chain: {chain_id}")

        # Normalize wallet address
        wallet_address = wallet_address.lower()

        # Generate cryptographically secure nonce
        nonce = secrets.token_hex(16)

        # Calculate expiration
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=NONCE_EXPIRATION_MINUTES)

        logger.info("challenge_requested", extra={"wallet": wallet_address, "chain_id": chain_id})

        return {
            "nonce": nonce,
            "expires_at": expires_at.isoformat(),
            "expiration_minutes": NONCE_EXPIRATION_MINUTES,
        }

    async def login(self, wallet_address: str, chain_id: int, signature: str, nonce: str) -> dict:
        """
        Authenticate a wallet by verifying the signed nonce.

        Args:
            wallet_address: The wallet address
            chain_id: The blockchain chain ID
            signature: The signed message
            nonce: The nonce that was signed

        Returns:
            Dict with session_token, wallet profile, and expiration

        Raises:
            ValueError: If wallet address is invalid, signature is invalid, nonce is invalid, etc.
        """
        # Validate chain
        if chain_id not in SUPPORTED_CHAINS:
            raise ValueError(f"Unsupported chain: {chain_id}")

        # Normalize wallet address
        wallet_address = wallet_address.lower()

        # Get the session with the nonce
        session = await self.wallet_session_repository.get_by_nonce(nonce)
        if session is None:
            raise ValueError("Invalid or expired nonce")

        # Check if nonce has expired
        now = datetime.now(timezone.utc)
        # Handle timezone-aware comparison - SQLite may return naive datetimes
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            await self.wallet_session_repository.delete_by_nonce(nonce)
            raise ValueError("Nonce has expired")

        # Verify the signature
        is_valid = self.verifier.verify_signature(nonce, signature, wallet_address)
        if not is_valid:
            logger.warning(
                "invalid_signature",
                extra={"wallet": wallet_address, "chain_id": chain_id},
            )
            raise ValueError("Invalid signature")

        # Delete the used nonce (single-use)
        await self.wallet_session_repository.delete_by_nonce(nonce)

        # Get or create wallet
        wallet = await self.wallet_repository.get_by_wallet_address(wallet_address)
        if wallet is None:
            wallet = await self.wallet_repository.create(wallet_address, chain_id)
        else:
            # Verify chain ID matches
            if wallet.chain_id != chain_id:
                raise ValueError(f"Wallet registered for chain {wallet.chain_id}, not {chain_id}")

        # Update last login
        wallet = await self.wallet_repository.update_last_login(wallet.id)

        # Generate session token
        session_token = secrets.token_urlsafe(32)
        session_expires_at = now + timedelta(hours=SESSION_EXPIRATION_HOURS)

        # Create session record
        session = await self.wallet_session_repository.create(
            wallet_id=wallet.id,
            nonce=nonce,  # Store original nonce for reference (already deleted above)
            session_token=session_token,
            expires_at=session_expires_at,
        )

        logger.info("login_successful", extra={"wallet": wallet_address, "chain_id": chain_id})

        return {
            "session_token": session_token,
            "wallet": {
                "id": str(wallet.id),
                "wallet_address": wallet.wallet_address,
                "chain_id": wallet.chain_id,
                "first_seen_at": wallet.first_seen_at.isoformat(),
                "last_login_at": wallet.last_login_at.isoformat() if wallet.last_login_at else None,
                "created_at": wallet.created_at.isoformat(),
            },
            "expires_at": session_expires_at.isoformat(),
            "expiration_hours": SESSION_EXPIRATION_HOURS,
        }

    async def logout(self, session_token: str) -> None:
        """
        Revoke a session token.

        Args:
            session_token: The session token to revoke
        """
        await self.wallet_session_repository.delete_by_session_token(session_token)
        logger.info("logout_successful")

    async def get_authenticated_wallet(self, session_token: str) -> Wallet | None:
        """
        Get the wallet associated with a valid session token.

        Args:
            session_token: The session token

        Returns:
            Wallet object if token is valid and not expired, None otherwise
        """
        session = await self.wallet_session_repository.get_by_session_token(session_token)
        if session is None:
            return None

        # Check if session has expired
        now = datetime.now(timezone.utc)
        # Handle timezone-aware comparison - SQLite may return naive datetimes
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            await self.wallet_session_repository.delete_by_session_token(session_token)
            return None

        # Get wallet
        wallet = await self.wallet_repository.get_by_id(session.wallet_id)
        return wallet
