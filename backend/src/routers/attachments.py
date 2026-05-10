"""Attachment file serving endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import Attachment

router = APIRouter(tags=["attachments"])
settings = get_settings()


@router.get("/attachments/{attachment_id}/file")
def get_attachment_file(attachment_id: int, db: Session = Depends(get_db)):
    attachment = db.get(Attachment, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if not attachment.file_path:
        raise HTTPException(status_code=404, detail="Attachment file path not set")

    file_path = (settings.attachment_dir_path / attachment.file_path).resolve()
    if not str(file_path).startswith(str(settings.attachment_dir_path.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Attachment file not found on disk")

    return FileResponse(
        path=str(file_path),
        filename=attachment.filename,
        media_type=attachment.content_type or "application/octet-stream",
    )
