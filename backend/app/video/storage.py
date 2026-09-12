from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile


class FileStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or os.getenv("VIDEO_STORAGE_DIR", "./videos"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _safe_name(self, filename: str) -> str:
        stem = Path(filename).stem
        suffix = Path(filename).suffix.lower()
        return f"{stem}{suffix}"

    def save_upload(self, upload: UploadFile) -> tuple[str, str]:
        if not upload.filename:
            raise ValueError("Missing filename")
        return self.save_upload_from_bytes(upload.file.read(), upload.filename)

    def save_upload_from_bytes(self, content: bytes, filename: str) -> tuple[str, str]:
        target_name = self._safe_name(filename)
        target_path = self.base_dir / target_name
        if target_path.exists():
            stem = Path(filename).stem
            suffix = Path(filename).suffix.lower()
            target_name = f"{stem}-copy{suffix}"
            target_path = self.base_dir / target_name

        with target_path.open("wb") as handle:
            handle.write(content)
        return str(target_path), target_name

    def get_path(self, filename: str) -> str:
        return str(self.base_dir / filename)

    def exists(self, filename: str) -> bool:
        return (self.base_dir / filename).exists()
