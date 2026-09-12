from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO


class StorageService(ABC):
    @abstractmethod
    async def ensure_bucket_exists(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def upload_video(self, folder: str, filename: str, stream: BinaryIO) -> str:
        raise NotImplementedError

    @abstractmethod
    async def upload_thumbnail(self, folder: str, filename: str, stream: BinaryIO) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_file(self, storage_path: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def file_exists(self, storage_path: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def generate_public_url(self, storage_path: str) -> str:
        raise NotImplementedError
