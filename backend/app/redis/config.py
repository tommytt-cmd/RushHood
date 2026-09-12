from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class RedisConfig:
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    db: int = int(os.getenv("REDIS_DB", "0"))
    password: str | None = os.getenv("REDIS_PASSWORD")
    url: str | None = os.getenv("REDIS_URL")
    pool_max_connections: int = int(os.getenv("REDIS_POOL_MAX_CONNECTIONS", "10"))
    reconnect_retries: int = int(os.getenv("REDIS_RECONNECT_RETRIES", "3"))
    reconnect_interval: float = float(os.getenv("REDIS_RECONNECT_INTERVAL_SECONDS", "1.0"))
