"""Buyers API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import BuyerRequest
from ..schemas import BuyerDetailResponse, BuyerRequestResponse, PaginatedResponse

router = APIRouter(tags=["buyers"])


@router.get("/buyers", response_model=PaginatedResponse)
def list_buyers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(BuyerRequest).filter(BuyerRequest.is_archived == False)
    total = query.count()
    pages = (total + per_page - 1) // per_page
    items = (
        query.order_by(BuyerRequest.first_seen_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedResponse(
        items=[BuyerRequestResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/buyers/{buyer_id}", response_model=BuyerDetailResponse)
def get_buyer(buyer_id: int, db: Session = Depends(get_db)):
    buyer = (
        db.query(BuyerRequest)
        .options(joinedload(BuyerRequest.matches), joinedload(BuyerRequest.email))
        .filter(BuyerRequest.id == buyer_id)
        .first()
    )
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer request not found")
    return buyer
