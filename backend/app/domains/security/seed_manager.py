from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base

logger = logging.getLogger("security")


class ServerSeed(Base):
    __tablename__ = "server_seeds"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    seed_value: Mapped[str] = mapped_column(String(128), nullable=False)
    active: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    rotated_at: Mapped[datetime | None] = mapped_column(nullable=True)


class ServerSeedRepository:
    def __init__(self, session: Any) -> None:
        self.session = session

    async def get_active_seed(self) -> ServerSeed | None:
        result = await self.session.execute(
            select(ServerSeed).where(ServerSeed.active.is_(True)).order_by(ServerSeed.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def create_seed(self, seed_value: str, active: bool = False) -> ServerSeed:
        seed = ServerSeed(seed_value=seed_value, active=active)
        self.session.add(seed)
        await self.session.commit()
        await self.session.refresh(seed)
        return seed

    async def rotate_seed(self, new_seed_value: str) -> ServerSeed:
        active_seed = await self.get_active_seed()
        if active_seed is not None:
            active_seed.active = False
            active_seed.rotated_at = datetime.now(timezone.utc)
            self.session.add(active_seed)
        seed = ServerSeed(seed_value=new_seed_value, active=True)
        self.session.add(seed)
        await self.session.commit()
        await self.session.refresh(seed)
        return seed


class SeedManager:
    def __init__(self, repository: ServerSeedRepository, rotation_interval_minutes: int = 60) -> None:
        self.repository = repository
        self.rotation_interval_minutes = rotation_interval_minutes

    async def get_active_seed(self) -> str:
        seed = await self.repository.get_active_seed()
        if seed is None:
            seed = await self._generate_seed(active=True)
        return seed.seed_value

    async def rotate_seed(self) -> str:
        new_seed = secrets.token_hex(32)
        seed_record = await self.repository.rotate_seed(new_seed)
        logger.info("seed_rotated", extra={"seed_id": str(seed_record.id), "rotated_at": seed_record.rotated_at.isoformat()})
        return seed_record.seed_value

    async def _generate_seed(self, active: bool = False) -> ServerSeed:
        seed_value = secrets.token_hex(32)
        return await self.repository.create_seed(seed_value=seed_value, active=active)

    async def archive_seeds(self) -> None:
        # nothing to do here, old seeds are retained in the table
        pass
