from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.treasury.model import Treasury


class TreasuryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self) -> Treasury:
        result = await self.session.execute(select(Treasury))
        treasury = result.scalar_one_or_none()
        if treasury is not None:
            return treasury

        treasury = Treasury()
        self.session.add(treasury)
        await self.session.commit()
        await self.session.refresh(treasury)
        return treasury

    async def get(self) -> Treasury:
        return await self.get_or_create()

    async def reserve(self, amount: int) -> Treasury:
        treasury = await self.get_or_create()
        if treasury.available_balance < amount:
            raise ValueError("Insufficient treasury funds")
        treasury.reserved_balance += amount
        treasury.recalc_available()
        treasury.updated_at = datetime.now(timezone.utc)
        self.session.add(treasury)
        await self.session.commit()
        await self.session.refresh(treasury)
        return treasury

    async def release(self, amount: int) -> Treasury:
        treasury = await self.get_or_create()
        treasury.reserved_balance = max(0, treasury.reserved_balance - amount)
        treasury.recalc_available()
        treasury.updated_at = datetime.now(timezone.utc)
        self.session.add(treasury)
        await self.session.commit()
        await self.session.refresh(treasury)
        return treasury

    async def collect_house_fee(self, amount: int) -> Treasury:
        treasury = await self.get_or_create()
        treasury.treasury_balance += amount
        treasury.recalc_available()
        treasury.updated_at = datetime.now(timezone.utc)
        self.session.add(treasury)
        await self.session.commit()
        await self.session.refresh(treasury)
        return treasury
