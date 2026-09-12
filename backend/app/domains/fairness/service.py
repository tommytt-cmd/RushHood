from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from app.domains.fairness.schema import FairnessVerifyResponse
from app.domains.security.commitment import calculate_commitment_hash
from app.domains.security.verifier import CommitmentVerifier
from app.repositories.round_repository import RoundRepository


class FairnessService:
    def __init__(
        self,
        round_repository: RoundRepository,
        verifier: CommitmentVerifier,
        commitment_repository: Any,
    ) -> None:
        self.round_repository = round_repository
        self.verifier = verifier
        self.commitment_repository = commitment_repository

    async def get_round(self, round_id: str) -> dict[str, object]:
        round_model = await self.round_repository.get_by_id(UUID(round_id))
        if round_model is None:
            raise ValueError("Round not found")

        commitment_record = await self.commitment_repository.get_by_round_id(round_id)
        if commitment_record is None:
            raise ValueError("Commitment not found")

        return {
            "round_id": round_id,
            "commitment_hash": commitment_record.commitment_hash,
            "threshold": getattr(round_model, "threshold", None),
            "algorithm_version": commitment_record.algorithm_version,
            "difficulty_profile": getattr(round_model, "difficulty_profile", None),
            "settlement_status": round_model.status.value,
        }

    async def verify(self, round_id: str) -> FairnessVerifyResponse:
        result = await self.verifier.verify(round_id)
        return FairnessVerifyResponse.model_validate(result)
