from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime, timedelta, timezone


class ReplayProtectionService:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = ttl_seconds
        self._signed_payloads: dict[str, datetime] = {}
        self._predictions: dict[str, datetime] = {}
        self._nonces: dict[str, datetime] = {}

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _purge_expired(self, store: dict[str, datetime]) -> None:
        cutoff = self._now() - timedelta(seconds=self.ttl_seconds)
        expired = [key for key, ts in store.items() if ts < cutoff]
        for key in expired:
            store.pop(key, None)

    def _hash(self, payload: str) -> str:
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def is_duplicate_signature(self, payload: str) -> bool:
        self._purge_expired(self._signed_payloads)
        digest = self._hash(payload)
        if digest in self._signed_payloads:
            return True
        self._signed_payloads[digest] = self._now()
        return False

    def is_duplicate_prediction(self, wallet_address: str, round_id: str, prediction: int, stake: int) -> bool:
        self._purge_expired(self._predictions)
        digest = self._hash(f"{wallet_address}:{round_id}:{prediction}:{stake}")
        if digest in self._predictions:
            return True
        self._predictions[digest] = self._now()
        return False

    def consume_nonce(self, nonce: str) -> bool:
        self._purge_expired(self._nonces)
        if nonce in self._nonces:
            return False
        self._nonces[nonce] = self._now()
        return True
