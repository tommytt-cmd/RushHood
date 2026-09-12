from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_video_repository
from app.storage.supabase_service import SupabaseStorageService
from app.services.upload_service import VideoUploadService


router = APIRouter(prefix="", tags=["upload"])


class UploadRequest(BaseModel):
    folder: str


@router.post("/upload", response_model=dict[str, object])
async def upload_processed_video(request: UploadRequest, session: AsyncSession = Depends(get_session)) -> dict[str, object]:
    storage = SupabaseStorageService()
    service = VideoUploadService(session, storage=storage)
    try:
        result = await service.upload_from_folder(request.folder)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "FolderNotFound", "message": "Processed folder not found"})
    except ValueError as exc:
        msg = str(exc)
        if msg == "DuplicateVideoId":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "DuplicateVideoId", "message": "Video already imported"})
        if msg == "DuplicateChecksum":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "DuplicateChecksum", "message": "Duplicate checksum"})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "InvalidData", "message": msg})
    except Exception as ex:
        msg = str(ex)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": "ImportFailed", "message": msg})
    return result
