"""
Shared pytest configuration for RushHour backend tests.
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database.base import Base
from app.domains.ledger.model import LedgerEntry  # noqa: F401
from app.models import bet as bet_model, player as player_model, replay_event, round as round_model, video as video_model, wallet as wallet_model  # noqa: F401
from app.models import stock as stock_model  # noqa: F401


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    """
    Create an async test database session with in-memory SQLite.
    Creates all tables and cleans up after the test.
    """
    # Use in-memory SQLite for fast tests
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session maker
    async_session_local = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session_local() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
