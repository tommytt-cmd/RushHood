from __future__ import annotations

from pydantic import BaseModel


class FairnessRoundResponse(BaseModel):
    round_id: str
    commitment_hash: str
    threshold: float | int | None
    algorithm_version: str
    difficulty_profile: str | None
    settlement_status: str | None


class FairnessVerifyRequest(BaseModel):
    round_id: str


class FairnessVerifyResponse(BaseModel):
    verification_result: str
    commitment_matches: bool
    algorithm_version: str
