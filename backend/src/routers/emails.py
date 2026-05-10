"""Emails API endpoints."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Email, GmailSyncState
from ..schemas import EmailResponse, PaginatedResponse
from ..services.gmail_client import is_gmail_configured

router = APIRouter(tags=["emails"])


class SyncResponse(BaseModel):
    processed: int
    message: str


class SyncStatusResponse(BaseModel):
    gmail_connected: bool
    last_sync_at: str | None = None
    last_sync_status: str | None = None
    last_sync_error: str | None = None
    total_emails: int = 0
    seller_listings: int = 0
    buyer_requests: int = 0
    irrelevant: int = 0
    parse_errors: int = 0
    recent_emails: list[EmailResponse] = []


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


@router.get("/emails/sync-status", response_model=SyncStatusResponse)
def sync_status(db: Session = Depends(get_db)):
    """Get Gmail sync status and email classification breakdown."""
    connected = is_gmail_configured()
    sync_state = db.query(GmailSyncState).first()

    # Classification counts
    counts = (
        db.query(Email.classification, func.count())
        .group_by(Email.classification)
        .all()
    )
    count_map = {cls: cnt for cls, cnt in counts}

    # Recent emails (last 10)
    recent = (
        db.query(Email)
        .order_by(Email.processed_at.desc())
        .limit(10)
        .all()
    )

    return SyncStatusResponse(
        gmail_connected=connected,
        last_sync_at=sync_state.last_sync_at.isoformat() if sync_state and sync_state.last_sync_at else None,
        last_sync_status=sync_state.last_sync_status if sync_state else None,
        last_sync_error=sync_state.last_sync_error if sync_state else None,
        total_emails=sum(count_map.values()),
        seller_listings=count_map.get("seller_listing", 0),
        buyer_requests=count_map.get("buyer_request", 0),
        irrelevant=count_map.get("irrelevant", 0),
        parse_errors=count_map.get("parse_error", 0),
        recent_emails=[EmailResponse.model_validate(e) for e in recent],
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
