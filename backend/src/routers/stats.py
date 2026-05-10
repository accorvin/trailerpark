"""Dashboard summary stats endpoint."""

import os
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import BuyerRequest, Listing, Match
from ..schemas import StatsResponse

router = APIRouter(tags=["stats"])
settings = get_settings()


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    active_listings = (
        db.query(Listing).filter(Listing.is_archived == False).count()
    )
    deals_count = (
        db.query(Listing)
        .filter(Listing.is_deal == True, Listing.is_archived == False)
        .count()
    )
    buyers_count = (
        db.query(BuyerRequest).filter(BuyerRequest.is_archived == False).count()
    )
    matches_count = db.query(Match).count()

    # Calculate attachment storage
    attachment_bytes = 0
    att_dir = settings.attachment_dir_path
    if att_dir.exists():
        for dirpath, dirnames, filenames in os.walk(att_dir):
            for f in filenames:
                attachment_bytes += Path(dirpath, f).stat().st_size

    return StatsResponse(
        active_listings=active_listings,
        deals_count=deals_count,
        buyers_count=buyers_count,
        matches_count=matches_count,
        attachment_storage_bytes=attachment_bytes,
    )
