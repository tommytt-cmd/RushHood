from __future__ import annotations

import contextvars
from typing import Any

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return request_id_var.get()


def set_request_id(request_id: str | None) -> None:
    request_id_var.set(request_id)
