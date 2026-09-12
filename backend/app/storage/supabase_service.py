from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import BinaryIO

from supabase import create_client

from app.storage.service import StorageService


class SupabaseStorageService(StorageService):
    def __init__(self, url: str | None = None, key: str | None = None, bucket: str | None = None) -> None:
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.bucket = bucket or os.getenv("SUPABASE_BUCKET", "processed-videos")
        if not self.url or not self.key:
            raise ValueError("Supabase storage configuration is required")
        self.client = create_client(self.url, self.key)

    async def ensure_bucket_exists(self) -> None:
        # Supabase bucket management is not async in the client, but this is service-layer only.
        buckets = self.client.storage.list_buckets()
        if not any(bucket.name == self.bucket for bucket in buckets):
            self.client.storage.create_bucket(self.bucket)

    async def upload_video(self, folder: str, filename: str, stream: BinaryIO) -> str:
        key = f"{folder}/{filename}"
        # Without this Supabase stores the object as text/plain. Browsers then
        # reject the URL as a media source even though its filename is .mp4.
        self.client.storage.from_(self.bucket).upload(
            key,
            stream.read(),
            file_options={"content-type": "video/mp4"},
        )
        return key

    async def upload_thumbnail(self, folder: str, filename: str, stream: BinaryIO) -> str | None:
        if stream is None:
            return None
        key = f"{folder}/{filename}"
        self.client.storage.from_(self.bucket).upload(
            key,
            stream.read(),
            file_options={"content-type": "image/jpeg"},
        )
        return key

    async def delete_file(self, storage_path: str) -> None:
        self.client.storage.from_(self.bucket).remove([storage_path])

    async def file_exists(self, storage_path: str) -> bool:
        result = self.client.storage.from_(self.bucket).list(path=storage_path.rsplit("/", 1)[0] if "/" in storage_path else "")
        return any(item.name == Path(storage_path).name for item in result.data)

    async def generate_public_url(self, storage_path: str) -> str:
        return self.client.storage.from_(self.bucket).get_public_url(storage_path)
