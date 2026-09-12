from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SecurityEvent(BaseModel):
    event: str


class CommitmentPublishedEvent(SecurityEvent):
    event: Literal["commitment_published"] = "commitment_published"
    round_id: str
    commitment_hash: str
    algorithm_version: str


class SeedRotatedEvent(SecurityEvent):
    event: Literal["seed_rotated"] = "seed_rotated"
    seed_id: str


class AuditRecordedEvent(SecurityEvent):
    event: Literal["audit_recorded"] = "audit_recorded"
    actor: str
    action: str
    resource: str
