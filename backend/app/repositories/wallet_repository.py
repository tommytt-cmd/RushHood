from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet, WalletSession


class WalletRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_wallet_address(self, wallet_address: str) -> Wallet | None:
        result = await self.session.execute(select(Wallet).where(Wallet.wallet_address == wallet_address))
        return result.scalar_one_or_none()

    async def get_by_id(self, wallet_id: UUID) -> Wallet | None:
        result = await self.session.execute(select(Wallet).where(Wallet.id == wallet_id))
        return result.scalar_one_or_none()

    async def create(self, wallet_address: str, chain_id: int) -> Wallet:
        wallet = Wallet(wallet_address=wallet_address, chain_id=chain_id)
        self.session.add(wallet)
        await self.session.commit()
        await self.session.refresh(wallet)
        return wallet

    async def update_last_login(self, wallet_id: UUID) -> Wallet:
        wallet = await self.get_by_id(wallet_id)
        if wallet is None:
            raise ValueError(f"Wallet {wallet_id} not found")
        wallet.last_login_at = datetime.now(datetime.now().astimezone().tzinfo or datetime.utcnow().tzinfo)
        await self.session.commit()
        await self.session.refresh(wallet)
        return wallet


class WalletSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, wallet_id: UUID, nonce: str, session_token: str, expires_at: datetime) -> WalletSession:
        session = WalletSession(
            wallet_id=wallet_id,
            nonce=nonce,
            session_token=session_token,
            expires_at=expires_at,
        )
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def get_by_session_token(self, session_token: str) -> WalletSession | None:
        result = await self.session.execute(
            select(WalletSession).where(WalletSession.session_token == session_token)
        )
        return result.scalar_one_or_none()

    async def get_by_nonce(self, nonce: str) -> WalletSession | None:
        result = await self.session.execute(select(WalletSession).where(WalletSession.nonce == nonce))
        return result.scalar_one_or_none()

    async def delete_by_nonce(self, nonce: str) -> None:
        await self.session.execute(delete(WalletSession).where(WalletSession.nonce == nonce))
        await self.session.commit()

    async def delete_expired(self) -> None:
        await self.session.execute(delete(WalletSession).where(WalletSession.expires_at <= datetime.utcnow()))
        await self.session.commit()

    async def delete_by_session_token(self, session_token: str) -> None:
        await self.session.execute(delete(WalletSession).where(WalletSession.session_token == session_token))
        await self.session.commit()
