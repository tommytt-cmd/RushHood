from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging
from time import sleep
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from web3 import Web3

from app.repositories.stock_repository import StockRepository


STOCK_VAULT_ABI = [
    {"type": "event", "name": "StockReceived", "anonymous": False, "inputs": [{"indexed": True, "name": "roundId", "type": "uint256"}, {"indexed": True, "name": "stockToken", "type": "address"}, {"indexed": False, "name": "amount", "type": "uint256"}]},
    {"type": "event", "name": "RoundFinalized", "anonymous": False, "inputs": [{"indexed": True, "name": "roundId", "type": "uint256"}]},
    {"type": "event", "name": "WinnerClaimed", "anonymous": False, "inputs": [{"indexed": True, "name": "roundId", "type": "uint256"}, {"indexed": True, "name": "winner", "type": "address"}, {"indexed": True, "name": "stockToken", "type": "address"}, {"indexed": False, "name": "amount", "type": "uint256"}]},
    {"type": "function", "name": "getRoundInfo", "stateMutability": "view", "inputs": [{"type": "uint256"}], "outputs": [{"type": "bool"}, {"type": "bool"}, {"type": "uint256"}, {"type": "uint256"}]},
    {"type": "function", "name": "getWinnerAt", "stateMutability": "view", "inputs": [{"type": "uint256"}, {"type": "uint256"}], "outputs": [{"type": "address"}]},
    {"type": "function", "name": "getWinnerContribution", "stateMutability": "view", "inputs": [{"type": "uint256"}, {"type": "address"}], "outputs": [{"type": "uint256"}]},
    {"type": "function", "name": "calculateEntitlement", "stateMutability": "view", "inputs": [{"type": "uint256"}, {"type": "address"}, {"type": "address"}], "outputs": [{"type": "uint256"}, {"type": "uint256"}, {"type": "uint256"}]},
]
ERC20_ABI = [{"type": "function", "name": "symbol", "stateMutability": "view", "inputs": [], "outputs": [{"type": "string"}]}, {"type": "function", "name": "decimals", "stateMutability": "view", "inputs": [], "outputs": [{"type": "uint8"}]}]


class StockVaultIndexer:
    """Read-only StockVault event indexer.

    It may be safely replayed from ``start_block``: unique keys on round/token,
    reward, and transaction hash make its writes idempotent.  The index is a
    cache; every reward figure is refreshed using `calculateEntitlement`.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], rpc_url: str, vault_address: str, start_block: int = 0) -> None:
        self.session_factory = session_factory
        self.start_block = start_block
        self.vault_address = Web3.to_checksum_address(vault_address)
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.vault = self.w3.eth.contract(address=self.vault_address, abi=STOCK_VAULT_ABI)

    async def sync_once(self, to_block: int | str = "latest") -> None:
        # Resolve "latest" once.  Advancing the checkpoint to a moving latest
        # block could otherwise skip events that arrive during this sync.
        target_block = (
            await asyncio.to_thread(lambda: self.w3.eth.block_number)
            if to_block == "latest"
            else int(to_block)
        )
        async with self.session_factory() as session:
            repository = StockRepository(session)
            last_indexed_block = await repository.get_last_indexed_block(self.vault_address)

        from_block = self.start_block if last_indexed_block is None else last_indexed_block + 1
        if from_block > target_block:
            return

        events = await asyncio.to_thread(self._read_events, from_block, target_block)
        for event in events:
            async with self.session_factory() as session:
                await self._handle_event(StockRepository(session), event)

        # If any event handler failed, this line is not reached. The next run
        # repeats the range; repository upserts make that recovery safe.
        async with self.session_factory() as session:
            await StockRepository(session).set_last_indexed_block(
                self.vault_address, target_block
            )

    def _read_events(self, from_block: int, to_block: int) -> list[object]:
        """Read logs while chunking the block range to avoid provider errors.

        Some RPC providers return internal errors for very large eth_getLogs
        requests. This helper breaks the full range into manageable windows and
        retries failed windows with backoff, reducing window size when needed.
        """
        logger = logging.getLogger(__name__)
        logs: list[object] = []

        # Choose conservative defaults; tune if your provider supports larger ranges.
        MAX_CHUNK = 5000
        MIN_CHUNK = 50
        MAX_RETRIES = 3

        event_types = (self.vault.events.StockReceived, self.vault.events.RoundFinalized, self.vault.events.WinnerClaimed)

        for event_type in event_types:
            start = int(from_block)
            target = int(to_block)
            chunk = MAX_CHUNK
            while start <= target:
                end = min(start + chunk - 1, target)
                attempt = 0
                while True:
                    try:
                        fetched = event_type().get_logs(from_block=start, to_block=end)
                        logs.extend(fetched)
                        break
                    except Exception as exc:  # pragma: no cover - provider/runtime failures
                        attempt += 1
                        logger.warning("get_logs failed for %s:%s-%s (attempt %s): %s", getattr(event_type, '__name__', 'event'), start, end, attempt, exc)
                        if attempt <= MAX_RETRIES:
                            # exponential backoff before retrying same window
                            sleep(0.5 * (2 ** (attempt - 1)))
                            continue
                        # If retries exhausted, reduce chunk size and retry the smaller window
                        if chunk > MIN_CHUNK:
                            old_chunk = chunk
                            chunk = max(MIN_CHUNK, chunk // 4)
                            logger.warning("Reducing chunk size from %s to %s and retrying window %s-%s", old_chunk, chunk, start, end)
                            # do not advance start/end yet; recalc end with smaller chunk and reset attempts
                            end = min(start + chunk - 1, target)
                            attempt = 0
                            continue
                        # If we've already reduced to MIN_CHUNK and still failing, raise
                        logger.exception("Persistent get_logs failure for window %s-%s", start, end)
                        raise
                start = end + 1

        return sorted(logs, key=lambda item: (item["blockNumber"], item["logIndex"]))

    async def _handle_event(self, repository: StockRepository, event: object) -> None:
        name = event["event"]
        args = event["args"]
        round_number = int(args["roundId"])
        round_model = await repository.get_round_by_number(round_number)
        if round_model is None:
            return  # The game round has not been indexed locally yet; replay is safe.
        if name == "StockReceived":
            address = str(args["stockToken"]).lower()
            token = await repository.get_or_create_token(address, *await asyncio.to_thread(self._token_metadata, address))
            await repository.upsert_round_stock(round_model.id, token.id, int(args["amount"]), event["transactionHash"].hex())
        elif name == "WinnerClaimed":
            winner = str(args["winner"]).lower()
            address = str(args["stockToken"]).lower()
            player = await repository.get_player(winner)
            token = await repository.get_token(address)
            if token is None:
                token = await repository.get_or_create_token(address, *await asyncio.to_thread(self._token_metadata, address))
            if player is not None:
                await repository.record_claim(
                    round_id=round_model.id,
                    player_id=player.id,
                    token_id=token.id,
                    amount=int(args["amount"]),
                    tx_hash=event["transactionHash"].hex(),
                )
        await self._sync_round(repository, round_model, round_number)

    def _token_metadata(self, address: str) -> tuple[str, int]:
        contract = self.w3.eth.contract(address=Web3.to_checksum_address(address), abi=ERC20_ABI)
        try:
            return str(contract.functions.symbol().call()), int(contract.functions.decimals().call())
        except Exception:
            return address[:10], 18

    async def _sync_round(self, repository: StockRepository, round_model: object, round_number: int) -> None:
        created, finalized, total, winner_count = await asyncio.to_thread(self.vault.functions.getRoundInfo(round_number).call)
        if not created:
            return
        stocks = await repository.stocks_for_round(round_model.id)
        for index in range(int(winner_count)):
            winner = str(await asyncio.to_thread(self.vault.functions.getWinnerAt(round_number, index).call)).lower()
            player = await repository.get_player(winner)
            if player is None:
                continue
            contribution = int(await asyncio.to_thread(self.vault.functions.getWinnerContribution(round_number, winner).call))
            for _, token in stocks:
                entitled, claimed, _ = await asyncio.to_thread(self.vault.functions.calculateEntitlement(round_number, token.token_address, winner).call)
                await repository.upsert_reward(round_id=round_model.id, player_id=player.id, token_id=token.id, contribution=contribution, total_contribution=int(total), entitlement=int(entitled), claimed=int(claimed))
