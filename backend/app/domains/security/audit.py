from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, String, select
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource: Mapped[str] = mapped_column(String(128), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class AuditRepository:
    def __init__(self, session: Any) -> None:
        self.session = session

    async def append(self, actor: str, action: str, resource: str, details: dict | None = None) -> AuditLog:
        entry = AuditLog(
            actor=actor,
            action=action,
            resource=resource,
            details=details or {},
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def list(self, limit: int = 100) -> list[AuditLog]:
        result = await self.session.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
