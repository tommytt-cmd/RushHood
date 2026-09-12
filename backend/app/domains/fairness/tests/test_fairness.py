import pytest

from app.domains.fairness.schema import FairnessRoundResponse, FairnessVerifyRequest, FairnessVerifyResponse


def test_fairness_schema_round_response():
    payload = {
        "round_id": "round-1",
        "commitment_hash": "abc",
        "threshold": 12,
        "algorithm_version": "v1",
        "difficulty_profile": "easy",
        "settlement_status": "FINISHED",
    }
    response = FairnessRoundResponse.model_validate(payload)
    assert response.round_id == "round-1"


def test_fairness_verify_schema():
    payload = {"round_id": "round-1"}
    request = FairnessVerifyRequest.model_validate(payload)
    response = FairnessVerifyResponse(verification_result="valid", commitment_matches=True, algorithm_version="v1")
    assert request.round_id == "round-1"
    assert response.commitment_matches is True
