"""Deals API endpoints."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Listing
from ..schemas import ListingResponse, PaginatedResponse

router = APIRouter(tags=["deals"])


class RunResponse(BaseModel):
    message: str


@router.post("/deals/detect", response_model=RunResponse)
def run_deal_detection(db: Session = Depends(get_db)):
    """Manually trigger deal detection for all active listings."""
    from ..services.deal_detector import detect_deals_all

    deals_found = detect_deals_all(db)
    return RunResponse(message=f"Deal detection complete: {deals_found} deal(s) found")


@router.get("/deals", response_model=PaginatedResponse)
def list_deals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Listing)
        .filter(Listing.is_deal == True, Listing.is_archived == False)
    )
    total = query.count()
    pages = (total + per_page - 1) // per_page
    items = (
        query.order_by(Listing.deal_savings.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedResponse(
        items=[ListingResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )
