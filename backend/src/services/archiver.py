"""Auto-archive logic for old listings and buyer requests."""

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import BuyerRequest, Listing

logger = logging.getLogger(__name__)
settings = get_settings()


def archive_old(db: Session) -> int:
    """Archive listings and buyer requests older than ARCHIVE_DAYS.

    Returns the total number of items archived.
    """
    cutoff = datetime.now() - timedelta(days=settings.ARCHIVE_DAYS)
    now = datetime.now()
    archived = 0

    # Archive old listings
    old_listings = (
        db.query(Listing)
        .filter(Listing.is_archived == False, Listing.first_seen_at < cutoff)
        .all()
    )
    for listing in old_listings:
        listing.is_archived = True
        listing.archived_at = now
        archived += 1

    # Archive old buyer requests
    old_buyers = (
        db.query(BuyerRequest)
        .filter(BuyerRequest.is_archived == False, BuyerRequest.first_seen_at < cutoff)
        .all()
    )
    for buyer in old_buyers:
        buyer.is_archived = True
        buyer.archived_at = now
        archived += 1

    if archived > 0:
        db.commit()
        logger.info("Archived %d items (cutoff: %s)", archived, cutoff.isoformat())

    return archived
