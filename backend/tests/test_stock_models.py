from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.player import Player
from app.models.round import Round
from app.models.stock import (
    RoundStock,
    StockClaim,
    StockIndexerCheckpoint,
    StockReward,
    StockToken,
)


@pytest.mark.asyncio
async def test_stock_token_address_is_unique(session):
    session.add(StockToken(token_address="0x" + "a" * 40, symbol="TSLA", decimals=18))
    await session.commit()
    session.add(StockToken(token_address="0x" + "a" * 40, symbol="TSLA", decimals=18))
    with pytest.raises(IntegrityError):
        await session.commit()


@pytest.mark.asyncio
async def test_round_stock_and_reward_are_unique(session):
    round_model = Round(round_number=128)
    player = Player(wallet_address="0x" + "b" * 40)
    token = StockToken(token_address="0x" + "c" * 40, symbol="NVDA", decimals=18)
    session.add_all([round_model, player, token])
    await session.commit()
    session.add(RoundStock(round_id=round_model.id, stock_token_id=token.id, amount_received=Decimal(10)))
    await session.commit()
    session.add(RoundStock(round_id=round_model.id, stock_token_id=token.id, amount_received=Decimal(10)))
    with pytest.raises(IntegrityError):
        await session.commit()

    await session.rollback()
    session.add(StockReward(round_id=round_model.id, player_id=player.id, stock_token_id=token.id, entitlement=Decimal(10), claimable_amount=Decimal(10)))
    await session.commit()
    session.add(StockReward(round_id=round_model.id, player_id=player.id, stock_token_id=token.id))
    with pytest.raises(IntegrityError):
        await session.commit()


@pytest.mark.asyncio
async def test_stock_claim_transaction_hash_is_immutable_and_unique(session):
    round_model = Round(round_number=129)
    player = Player(wallet_address="0x" + "d" * 40)
    token = StockToken(token_address="0x" + "e" * 40, symbol="AAPL", decimals=18)
    session.add_all([round_model, player, token])
    await session.commit()
    tx_hash = "0x" + "f" * 64
    session.add(StockClaim(round_id=round_model.id, player_id=player.id, stock_token_id=token.id, amount=Decimal(1), transaction_hash=tx_hash))
    await session.commit()
    session.add(StockClaim(round_id=round_model.id, player_id=player.id, stock_token_id=token.id, amount=Decimal(1), transaction_hash=tx_hash))
    with pytest.raises(IntegrityError):
        await session.commit()


@pytest.mark.asyncio
async def test_stock_indexer_checkpoint_is_keyed_by_vault_address(session):
    checkpoint = StockIndexerCheckpoint(
        vault_address="0x" + "1" * 40,
        last_indexed_block=12345,
    )
    session.add(checkpoint)
    await session.commit()

    session.add(
        StockIndexerCheckpoint(
            vault_address="0x" + "1" * 40,
            last_indexed_block=12346,
        )
    )
    with pytest.raises(IntegrityError):
        await session.commit()
