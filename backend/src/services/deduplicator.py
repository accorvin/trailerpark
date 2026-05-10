"""Duplicate listing detection."""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import Listing

logger = logging.getLogger(__name__)


def check_duplicate(db: Session, new_listing: Listing) -> Listing | None:
    """Check if a listing is a duplicate of an existing one.

    Returns the existing listing if duplicate found, None otherwise.
    """
    if not new_listing.make or not new_listing.model or new_listing.year is None:
        return None

    candidates = (
        db.query(Listing)
        .filter(
            Listing.id != new_listing.id,
            Listing.is_archived == False,
            Listing.make == new_listing.make,
            Listing.model == new_listing.model,
            Listing.year == new_listing.year,
        )
        .all()
    )

    for candidate in candidates:
        # Check mileage similarity (within 5%)
        if new_listing.mileage is not None and candidate.mileage is not None:
            mileage_diff = abs(new_listing.mileage - candidate.mileage)
            max_mileage = max(new_listing.mileage, candidate.mileage)
            if max_mileage > 0 and mileage_diff / max_mileage > 0.05:
                continue
        elif new_listing.mileage is not None or candidate.mileage is not None:
            # One has mileage, the other doesn't — still might be duplicate
            # but need price match instead
            pass

        # Check price similarity (within 10%) — skip if either is null
        if new_listing.price is not None and candidate.price is not None:
            price_diff = abs(float(new_listing.price) - float(candidate.price))
            max_price = max(float(new_listing.price), float(candidate.price))
            if max_price > 0 and price_diff / max_price > 0.10:
                continue
        elif new_listing.price is None and candidate.price is None:
            # Both null: rely on make+model+year+mileage match
            if new_listing.mileage is None or candidate.mileage is None:
                continue

        # If we got here, it's a match
        logger.info(
            "Duplicate detected: listing %d matches existing listing %d (%s %s %d)",
            new_listing.id, candidate.id,
            candidate.make, candidate.model, candidate.year,
        )
        return candidate

    return None


def deduplicate_listing(db: Session, new_listing: Listing) -> bool:
    """Check for duplicates and update existing listing if found.

    Returns True if duplicate was found and handled.
    """
    existing = check_duplicate(db, new_listing)
    if existing is None:
        return False

    # Update existing listing's last_seen_at
    existing.last_seen_at = datetime.now()

    # If the new listing has a price and the existing doesn't, update it
    if new_listing.price is not None and existing.price is None:
        existing.price = new_listing.price

    # Remove the duplicate new listing
    db.delete(new_listing)
    db.commit()

    return True
