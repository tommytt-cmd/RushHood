from __future__ import annotations

from app.domains.treasury.repository import TreasuryRepository


class TreasuryService:
    def __init__(self, treasury_repository: TreasuryRepository) -> None:
        self.treasury_repository = treasury_repository

    async def get_treasury(self):
        return await self.treasury_repository.get()

    async def reserve_funds(self, amount: int):
        return await self.treasury_repository.reserve(amount)

    async def release_funds(self, amount: int):
        return await self.treasury_repository.release(amount)

    async def collect_house_fee(self, amount: int):
        return await self.treasury_repository.collect_house_fee(amount)
