"""Emails API endpoints."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Email
from ..schemas import EmailResponse, PaginatedResponse
from ..services.gmail_client import is_gmail_configured

router = APIRouter(tags=["emails"])


class SyncResponse(BaseModel):
    processed: int
    message: str


@router.get("/emails", response_model=PaginatedResponse)
def list_emails(
    classification: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Email)

    if classification:
        query = query.filter(Email.classification == classification)

    total = query.count()
    pages = (total + per_page - 1) // per_page
    items = (
        query.order_by(Email.processed_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedResponse(
        items=[EmailResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.post("/emails/sync", response_model=SyncResponse)
def sync_emails(db: Session = Depends(get_db)):
    if not is_gmail_configured():
        return SyncResponse(
            processed=0,
            message="Gmail not connected. Please log in to connect your Gmail account.",
        )

    from ..services.email_ingestion import scan_emails

    processed = scan_emails(db)
    return SyncResponse(
        processed=processed,
        message=f"Processed {processed} new email(s)",
    )
