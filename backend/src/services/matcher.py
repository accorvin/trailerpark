"""Buyer-seller matching algorithm."""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import BuyerRequest, Listing, Match

logger = logging.getLogger(__name__)

MATCH_THRESHOLD = 0.6


def score_match(buyer: BuyerRequest, listing: Listing) -> float:
    """Score a buyer-listing pair. Returns 0-1 score."""
    # vehicle_type is required match
    if not buyer.vehicle_type or not listing.vehicle_type:
        return 0.0
    if buyer.vehicle_type.lower() != listing.vehicle_type.lower():
        return 0.0

    score = 0.0

    # make match: +0.15
    if buyer.make and listing.make:
        if buyer.make.lower() == listing.make.lower():
            score += 0.15

    # model match: +0.25
    if buyer.model and listing.model:
        if buyer.model.lower() == listing.model.lower():
            score += 0.25

    # year in range: +0.2
    if listing.year is not None:
        year_ok = True
        if buyer.year_min is not None and listing.year < buyer.year_min:
            year_ok = False
        if buyer.year_max is not None and listing.year > buyer.year_max:
            year_ok = False
        if year_ok and (buyer.year_min is not None or buyer.year_max is not None):
            score += 0.2

    # mileage under max: +0.15
    if buyer.mileage_max is not None and listing.mileage is not None:
        if listing.mileage <= buyer.mileage_max:
            score += 0.15

    # price in range: +0.2
    if listing.price is not None:
        price_ok = True
        if buyer.price_min is not None and float(listing.price) < float(buyer.price_min):
            price_ok = False
        if buyer.price_max is not None and float(listing.price) > float(buyer.price_max):
            price_ok = False
        if price_ok and (buyer.price_min is not None or buyer.price_max is not None):
            score += 0.2

    # engine match: +0.05
    if buyer.engine_type and listing.engine_type:
        if buyer.engine_type.lower() == listing.engine_type.lower():
            score += 0.05

    return score


def match_new_listings(db: Session, new_listing_ids: list[int]) -> int:
    """Match new listings against existing active buyers. Returns count of new matches."""
    buyers = (
        db.query(BuyerRequest)
        .filter(BuyerRequest.is_archived == False)
        .all()
    )
    listings = (
        db.query(Listing)
        .filter(Listing.id.in_(new_listing_ids))
        .all()
    )

    return _create_matches(db, buyers, listings)


def match_new_buyers(db: Session, new_buyer_ids: list[int]) -> int:
    """Match new buyers against existing active listings. Returns count of new matches."""
    buyers = (
        db.query(BuyerRequest)
        .filter(BuyerRequest.id.in_(new_buyer_ids))
        .all()
    )
    listings = (
        db.query(Listing)
        .filter(Listing.is_archived == False)
        .all()
    )

    return _create_matches(db, buyers, listings)


def match_all(db: Session) -> int:
    """Full re-matching of all active buyers against all active listings."""
    # Clear existing matches
    db.query(Match).delete()

    buyers = (
        db.query(BuyerRequest)
        .filter(BuyerRequest.is_archived == False)
        .all()
    )
    listings = (
        db.query(Listing)
        .filter(Listing.is_archived == False)
        .all()
    )

    count = _create_matches(db, buyers, listings)
    logger.info("Full re-matching: %d matches from %d buyers x %d listings", count, len(buyers), len(listings))
    return count


def _create_matches(db: Session, buyers: list[BuyerRequest], listings: list[Listing]) -> int:
    """Score and create matches above threshold. Returns count."""
    created = 0
    now = datetime.now()

    for buyer in buyers:
        for listing in listings:
            score = score_match(buyer, listing)
            if score < MATCH_THRESHOLD:
                continue

            # Check if match already exists
            existing = (
                db.query(Match)
                .filter(
                    Match.buyer_request_id == buyer.id,
                    Match.listing_id == listing.id,
                )
                .first()
            )
            if existing:
                existing.score = score
                existing.matched_at = now
                continue

            match = Match(
                buyer_request_id=buyer.id,
                listing_id=listing.id,
                score=score,
                matched_at=now,
            )
            db.add(match)
            created += 1

    db.commit()
    return created
