from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from ..config import PROCESSED_DIR

router = APIRouter(prefix="/api/media")


@router.get("/{filename}")
def get_media(filename: str):
    safe = Path(filename).name
    path = PROCESSED_DIR / safe
    if not path.exists():
        raise HTTPException(404, "Media not found")
    return FileResponse(path, media_type="video/mp4", filename=safe)
