"""Emails debug/admin API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Email
from ..schemas import EmailResponse, PaginatedResponse

router = APIRouter(tags=["emails"])


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
