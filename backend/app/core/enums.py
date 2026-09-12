from enum import Enum


class RoundStatus(str, Enum):
    WAITING = "WAITING"
    OPEN = "OPEN"
    LOCKED = "LOCKED"
    LIVE = "LIVE"
    SETTLED = "SETTLED"
    FINISHED = "FINISHED"


class BetStatus(str, Enum):
    PENDING = "PENDING"
    WON = "WON"
    LOST = "LOST"


class SettlementStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    SUBMITTING = "SUBMITTING"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class BuybackStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    FINALIZING = "FINALIZING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class FinancialReconciliationStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class VideoStatus(str, Enum):
    UPLOADING = "UPLOADING"
    READY = "READY"
    IN_USE = "IN_USE"
    USED = "USED"
    FAILED = "FAILED"
