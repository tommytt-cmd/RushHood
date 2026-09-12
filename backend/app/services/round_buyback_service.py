from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone

from app.core.enums import BuybackStatus
from app.models.round import Round
from app.oracle.client import OracleClient, OracleConnectionError
from app.repositories.round_repository import RoundRepository
from app.settings import settings

logger = logging.getLogger("game")


class RoundBuybackService:
    """Execute and finalize a settled round's buyback exactly once.

    The on-chain round is already FINISHED after ``settleRound``; that is a
    contract prerequisite for a buyback. This service owns the separate
    backend financial-finalization state and makes it durable on ``Round``.
    """

    def __init__(self, round_repository: RoundRepository, source: OracleClient | None) -> None:
        if source is None:
            raise ValueError("ORACLE_ENABLED must be true when BUYBACK_ENABLED=true")
        if not settings.BUYBACK_CONTRACT_ADDRESS or not settings.BUYBACK_PRIVATE_KEY:
            raise ValueError("BUYBACK_CONTRACT_ADDRESS and BUYBACK_PRIVATE_KEY are required when BUYBACK_ENABLED=true")
        if settings.BUYBACK_EXECUTION_MODE not in {"testnet_mock", "mainnet"}:
            raise ValueError("BUYBACK_EXECUTION_MODE must be 'testnet_mock' or 'mainnet'")
        if settings.BUYBACK_EXECUTION_MODE == "mainnet" and settings.BUYBACK_MIN_OUTPUT_WEI <= 1:
            raise ValueError(
                "A protected BUYBACK_MIN_OUTPUT_WEI is required for mainnet; "
                "the testnet default of 1 must never be used for a real swap"
            )

        self.round_repository = round_repository
        # Use the keeper wallet (not the oracle wallet) for both transactions;
        # it must hold BUYBACK_ROLE on RushBetting and the manager.
        self.source = OracleClient(
            settings.ORACLE_RPC_URL,
            settings.ORACLE_CONTRACT_ADDRESS,
            private_key=settings.BUYBACK_PRIVATE_KEY,
        )
        artifact = "MockTestnetBuybackManager" if settings.BUYBACK_EXECUTION_MODE == "testnet_mock" else "RushBuybackManager"
        default_contract_json_path = settings.BUYBACK_CONTRACT_JSON_PATH or f"../contract/out/{artifact}.sol/{artifact}.json"
        self.manager = OracleClient(
            settings.ORACLE_RPC_URL,
            settings.BUYBACK_CONTRACT_ADDRESS,
            contract_json_path=default_contract_json_path,
            private_key=settings.BUYBACK_PRIVATE_KEY,
        )

        if not self.source.is_connected() or not self.manager.is_connected():
            raise OracleConnectionError("Buyback RPC is not connected")
        if self.source.get_chain_id() != self.manager.get_chain_id():
            raise OracleConnectionError("Buyback manager and RushBetting clients are on different chains")
        if str(self.manager.call_readonly("source")).lower() != self.source.contract_address.lower():
            raise OracleConnectionError("BUYBACK_CONTRACT_ADDRESS is not linked to ORACLE_CONTRACT_ADDRESS")

    async def process_round(self, round_model: Round) -> bool:
        return await asyncio.to_thread(self._process_round_sync, round_model)

    def _process_round_sync(self, round_model: Round) -> bool:
        # No session calls occur in this worker thread. The scheduler persists
        # the resulting fields on its own event-loop thread.
        if round_model.buyback_status in {BuybackStatus.CONFIRMED.value, BuybackStatus.NOT_REQUIRED.value}:
            return True
        if round_model.round_number is None:
            raise ValueError("Round number is required for buyback")

        onchain_round = self.source.get_round_struct(int(round_model.round_number))
        allocation = int(onchain_round.get("buybackAllocation", 0))
        if allocation == 0:
            return self._result(round_model, BuybackStatus.NOT_REQUIRED, allocation=0)

        # Reconcile a process restart after an execution transaction mined but
        # before its database state was persisted.
        if not bool(self.manager.call_readonly("roundBuybackExecuted", int(round_model.round_number))):
            function, args = self._execution_call(int(round_model.round_number), allocation)
            tx_hash = self.manager.send_transaction(function, *args)
            receipt = self.manager.wait_for_transaction_receipt(tx_hash, timeout=180)
            if self._receipt_status(receipt) != 1:
                return self._result(round_model, BuybackStatus.FAILED, allocation, error="buyback transaction reverted")
            round_model.buyback_execution_tx_hash = tx_hash

        round_model.buyback_status = BuybackStatus.EXECUTED.value
        rush_allocation = self.source.call_readonly("getRoundRushAllocation", int(round_model.round_number))
        if bool(rush_allocation[1]):
            return self._result(round_model, BuybackStatus.CONFIRMED, allocation)
        finalization_tx = self.source.send_transaction("finalizeRoundRushBuyback", int(round_model.round_number))
        receipt = self.source.wait_for_transaction_receipt(finalization_tx, timeout=180)
        if self._receipt_status(receipt) != 1:
            return self._result(round_model, BuybackStatus.FAILED, allocation, error="buyback finalization transaction reverted")
        round_model.buyback_finalization_tx_hash = finalization_tx
        return self._result(round_model, BuybackStatus.CONFIRMED, allocation)

    def _execution_call(self, round_number: int, allocation: int) -> tuple[str, tuple[int, ...]]:
        deadline = int(time.time()) + settings.BUYBACK_DEADLINE_SECONDS
        minimum_output = settings.BUYBACK_MIN_OUTPUT_WEI
        if minimum_output <= 0:
            raise ValueError("BUYBACK_MIN_OUTPUT_WEI must be positive")
        if settings.BUYBACK_EXECUTION_MODE == "testnet_mock":
            return "executeMockBuyback", (round_number, allocation, minimum_output, deadline)
        if settings.BUYBACK_MAINNET_PATH == "pons_curve":
            return "executePonsCurveBuyback", (round_number, allocation, minimum_output, deadline)
        if settings.BUYBACK_MAINNET_PATH == "graduated":
            return "executeGraduatedBuyback", (round_number, allocation, minimum_output, settings.BUYBACK_FEE_TIER, 0, deadline)
        raise ValueError("BUYBACK_MAINNET_PATH must be 'pons_curve' or 'graduated'")

    @staticmethod
    def _receipt_status(receipt) -> int:
        status = getattr(receipt, "status", None)
        if status is None:
            status = receipt.get("status")
        return int(status)

    @staticmethod
    def _result(round_model: Round, status: BuybackStatus, allocation: int, error: str | None = None) -> bool:
        round_model.buyback_status = status.value
        round_model.buyback_allocation_wei = allocation
        round_model.buyback_error_message = error
        round_model.buyback_attempts += 1
        if status in {BuybackStatus.CONFIRMED, BuybackStatus.NOT_REQUIRED}:
            round_model.buyback_confirmed_at = datetime.now(timezone.utc)
            round_model.buyback_error_message = None
            return True
        return False
