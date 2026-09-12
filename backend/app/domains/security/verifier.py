from __future__ import annotations

from typing import Any
from uuid import UUID

from app.domains.security.commitment import build_commitment_payload, calculate_commitment_hash
from app.domains.security.seed_manager import SeedManager
from app.repositories.round_repository import RoundRepository


class CommitmentVerifier:
    def __init__(
        self,
        round_repository: RoundRepository,
        seed_manager: SeedManager,
        commitment_repository: Any,
    ) -> None:
        self.round_repository = round_repository
        self.seed_manager = seed_manager
        self.commitment_repository = commitment_repository

    async def verify(self, round_id: str) -> dict[str, object]:
        round_model = await self.round_repository.get_by_id(UUID(round_id))
        if round_model is None:
            raise ValueError("Round not found")

        commitment_record = await self.commitment_repository.get_by_round_id(round_id)
        if commitment_record is None:
            raise ValueError("Commitment not found")

        # Use the active server seed only for deterministic recomputation of the committed hash.
        # In practice the seed manager must ensure the same seed value was active at generation time.
        server_seed = await self.seed_manager.get_active_seed()
        payload = build_commitment_payload(round_model, server_seed)
        expected = calculate_commitment_hash(payload)

        return {
            "round_id": round_id,
            "commitment_matches": expected == commitment_record.commitment_hash,
            "algorithm_version": commitment_record.algorithm_version,
            "verification_result": "valid" if expected == commitment_record.commitment_hash else "invalid",
        }
