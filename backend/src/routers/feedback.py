"""Feedback API endpoints for editing listings, buyer requests, and email operations."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import BuyerRequest, FieldCorrection, Listing
from ..schemas import (
    BuyerDetailResponse,
    BuyerRequestBase,
    BuyerRequestUpdate,
    FieldCorrectionResponse,
    ListingBase,
    ListingDetailResponse,
    ListingUpdate,
    PaginatedResponse,
    ReclassifyRequest,
    ReclassifyResponse,
    ReparseResponse,
)
from ..services.email_ingestion import reclassify_email, reparse_email
from ..services.glossary import auto_learn_entry, is_abbreviation_correction

router = APIRouter(tags=["feedback"])


@router.patch("/listings/{listing_id}", response_model=ListingDetailResponse)
def update_listing(listing_id: int, data: ListingUpdate, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Snapshot original data on first edit
    if not listing.user_edited:
        snapshot = ListingBase.model_validate(listing).model_dump(mode="json")
        listing.original_extracted_data = json.dumps(snapshot)

    updates = data.model_dump(exclude_unset=True)
    for field_name, new_value in updates.items():
        old_value = getattr(listing, field_name)
        old_str = str(old_value) if old_value is not None else None
        new_str = str(new_value) if new_value is not None else None

        if old_str != new_str:
            # Record correction
            correction = FieldCorrection(
                entity_type="listing",
                entity_id=listing.id,
                field_name=field_name,
                original_value=old_str,
                corrected_value=new_str,
            )
            db.add(correction)

            # Auto-learn abbreviation if applicable
            if is_abbreviation_correction(field_name, old_str, new_str):
                auto_learn_entry(db, old_str, new_str, category=field_name)

        setattr(listing, field_name, new_value)

    listing.user_edited = True
    listing.user_edited_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(listing)
    return _listing_detail_response(listing, db)


@router.patch("/buyer-requests/{buyer_id}", response_model=BuyerDetailResponse)
def update_buyer_request(buyer_id: int, data: BuyerRequestUpdate, db: Session = Depends(get_db)):
    buyer = db.query(BuyerRequest).filter(BuyerRequest.id == buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer request not found")

    if not buyer.user_edited:
        snapshot = BuyerRequestBase.model_validate(buyer).model_dump(mode="json")
        buyer.original_extracted_data = json.dumps(snapshot)

    updates = data.model_dump(exclude_unset=True)
    for field_name, new_value in updates.items():
        old_value = getattr(buyer, field_name)
        old_str = str(old_value) if old_value is not None else None
        new_str = str(new_value) if new_value is not None else None

        if old_str != new_str:
            correction = FieldCorrection(
                entity_type="buyer_request",
                entity_id=buyer.id,
                field_name=field_name,
                original_value=old_str,
                corrected_value=new_str,
            )
            db.add(correction)

            if is_abbreviation_correction(field_name, old_str, new_str):
                auto_learn_entry(db, old_str, new_str, category=field_name)

        setattr(buyer, field_name, new_value)

    buyer.user_edited = True
    buyer.user_edited_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(buyer)
    return buyer


@router.post("/emails/{email_id}/reparse", response_model=ReparseResponse)
def reparse(email_id: str, db: Session = Depends(get_db)):
    result = reparse_email(db, email_id)
    status = result.pop("status", 200)
    if status >= 400:
        raise HTTPException(status_code=status, detail=result.get("error", "Unknown error"))
    return result


@router.post("/emails/{email_id}/reclassify", response_model=ReclassifyResponse)
def reclassify(email_id: str, data: ReclassifyRequest, db: Session = Depends(get_db)):
    result = reclassify_email(db, email_id, data.classification)
    status = result.pop("status", 200)
    if status >= 400:
        raise HTTPException(status_code=status, detail=result.get("error", "Unknown error"))
    return result


@router.get("/feedback/corrections", response_model=PaginatedResponse)
def list_corrections(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(FieldCorrection).order_by(FieldCorrection.created_at.desc())
    total = query.count()
    pages = (total + per_page - 1) // per_page
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return PaginatedResponse(
        items=[FieldCorrectionResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


def _listing_detail_response(listing: Listing, db: Session) -> ListingDetailResponse:
    """Build a ListingDetailResponse from a Listing ORM object."""
    from ..models import Attachment
    from ..schemas import AttachmentResponse

    result = ListingDetailResponse.model_validate(listing)
    attachments = db.query(Attachment).filter(Attachment.email_id == listing.email_id).all()
    result.attachments = [AttachmentResponse.model_validate(a) for a in attachments]

    # Parse source_mapping JSON
    if listing.source_mapping:
        try:
            result.source_mappings = json.loads(listing.source_mapping)
        except (json.JSONDecodeError, TypeError):
            pass

    # Parse original_extracted_data JSON
    if listing.original_extracted_data:
        try:
            result.original_extracted_data = json.loads(listing.original_extracted_data)
        except (json.JSONDecodeError, TypeError):
            pass

    return result
