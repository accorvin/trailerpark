"""Listings API endpoints."""

import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Attachment, Listing
from ..schemas import ListingDetailResponse, ListingResponse, PaginatedResponse

router = APIRouter(tags=["listings"])


@router.get("/listings", response_model=PaginatedResponse)
def list_listings(
    vehicle_type: str | None = None,
    make: str | None = None,
    model: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    mileage_max: int | None = None,
    engine_type: str | None = None,
    location: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Listing).filter(Listing.is_archived == False)

    if vehicle_type:
        query = query.filter(Listing.vehicle_type.ilike(f"%{vehicle_type}%"))
    if make:
        query = query.filter(Listing.make.ilike(f"%{make}%"))
    if model:
        query = query.filter(Listing.model.ilike(f"%{model}%"))
    if year_min is not None:
        query = query.filter(Listing.year >= year_min)
    if year_max is not None:
        query = query.filter(Listing.year <= year_max)
    if price_min is not None:
        query = query.filter(Listing.price >= price_min)
    if price_max is not None:
        query = query.filter(Listing.price <= price_max)
    if mileage_max is not None:
        query = query.filter(Listing.mileage <= mileage_max)
    if engine_type:
        query = query.filter(Listing.engine_type.ilike(f"%{engine_type}%"))
    if location:
        query = query.filter(Listing.location.ilike(f"%{location}%"))

    if search:
        # Sanitize FTS5 special characters and operators
        safe_search = re.sub(r'[*"(){}^]', '', search)
        safe_search = ' '.join(
            word for word in safe_search.split()
            if word.upper() not in ('AND', 'OR', 'NOT', 'NEAR')
        )
        if not safe_search.strip():
            search = None
    if search:
        fts_query = text(
            "SELECT rowid FROM listings_fts WHERE listings_fts MATCH :search"
        )
        result = db.execute(fts_query, {"search": safe_search})
        matching_ids = [row[0] for row in result]
        if matching_ids:
            query = query.filter(Listing.id.in_(matching_ids))
        else:
            query = query.filter(False)  # No FTS matches

    total = query.count()
    pages = (total + per_page - 1) // per_page
    items = (
        query.order_by(Listing.first_seen_at.desc())
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


@router.get("/listings/{listing_id}", response_model=ListingDetailResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = (
        db.query(Listing)
        .options(joinedload(Listing.email))
        .filter(Listing.id == listing_id)
        .first()
    )
    if not listing:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Listing not found")

    attachments = (
        db.query(Attachment)
        .filter(Attachment.email_id == listing.email_id)
        .all()
    )

    result = ListingDetailResponse.model_validate(listing)
    from ..schemas import AttachmentResponse, EmailResponse
    result.attachments = [AttachmentResponse.model_validate(a) for a in attachments]
    return result


@router.get("/archive", response_model=PaginatedResponse)
def list_archived(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Listing).filter(Listing.is_archived == True)
    total = query.count()
    pages = (total + per_page - 1) // per_page
    items = (
        query.order_by(Listing.archived_at.desc())
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
