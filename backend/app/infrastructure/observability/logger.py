from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "route": getattr(record, "route", None),
            "domain": getattr(record, "domain", None),
            "event": getattr(record, "event", None),
            "duration": getattr(record, "duration", None),
        }
        return json.dumps(payload, default=str)


class FileFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        extra_fields = []
        for key in ("request_id", "route", "domain", "event", "duration"):
            value = getattr(record, key, None)
            if value is not None:
                extra_fields.append(f"{key}={value}")
        if extra_fields:
            return f"{formatted} | {' '.join(extra_fields)}"
        return formatted


def configure_logging(level: str | None = None) -> None:
    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())

    log_file_path = Path(os.getenv("LOG_FILE_PATH", "./logs/rushhour.log"))
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=str(log_file_path),
        maxBytes=int(os.getenv("LOG_FILE_MAX_BYTES", str(5 * 1024 * 1024))),
        backupCount=int(os.getenv("LOG_FILE_BACKUP_COUNT", "5")),
        encoding="utf-8",
    )
    file_formatter = FileFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    file_handler.setFormatter(file_formatter)

    root = logging.getLogger()
    root.handlers = [console_handler, file_handler]
    root.setLevel(getattr(logging, log_level, logging.INFO))

    logging.getLogger("uvicorn").handlers = []
    logging.getLogger("uvicorn").propagate = True
