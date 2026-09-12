from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.round import Round


class RoundCommitment(Base):
    __tablename__ = "round_commitments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    round_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    commitment_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(32), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


def build_commitment_payload(round_model: Round, server_seed: str) -> str:
    payload = {
        "round_id": str(round_model.id),
        "processed_video_id": str(round_model.video_id) if round_model.video_id else None,
        "threshold": getattr(round_model, "threshold", None),
        "algorithm_version": getattr(round_model, "algorithm_version", "v1"),
        "difficulty_profile": getattr(round_model, "difficulty_profile", None),
        "server_seed": server_seed,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def calculate_commitment_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
