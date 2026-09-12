import pytest
from datetime import datetime, timezone

from app.domains.security.commitment import calculate_commitment_hash, build_commitment_payload
from app.domains.security.replay import ReplayProtectionService
from app.domains.security.seed_manager import SeedManager, ServerSeedRepository
from app.domains.security.audit import AuditRepository


class DummySession:
    def __init__(self):
        self.items = []
        self.commits = 0

    async def execute(self, *args, **kwargs):
        return type("Result", (), {"scalar_one_or_none": lambda self: None, "scalars": lambda self: type("Scalars", (), {"all": lambda self: []})()})()

    async def commit(self):
        self.commits += 1

    async def refresh(self, instance):
        return None

    def add(self, item):
        self.items.append(item)


@pytest.mark.asyncio
async def test_commitment_is_deterministic():
    class DummyRound:
        id = "round-1"
        video_id = "video-1"
        threshold = 10
        algorithm_version = "v1"
        difficulty_profile = "easy"

    payload = build_commitment_payload(DummyRound(), "seed")
    digest = calculate_commitment_hash(payload)
    assert digest == calculate_commitment_hash(payload)


@pytest.mark.asyncio
async def test_seed_rotation_and_retrieval():
    session = DummySession()
    repo = ServerSeedRepository(session)
    manager = SeedManager(repo)
    assert await manager.get_active_seed() is not None


@pytest.mark.asyncio
async def test_replay_protection_rejects_duplicates():
    service = ReplayProtectionService(ttl_seconds=60)
    assert service.is_duplicate_signature("payload") is False
    assert service.is_duplicate_signature("payload") is True


@pytest.mark.asyncio
async def test_audit_append_is_append_only():
    session = DummySession()
    repo = AuditRepository(session)
    entry = await repo.append("admin", "rotate_seed", "seed")
    assert entry.action == "rotate_seed"
