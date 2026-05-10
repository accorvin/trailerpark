"""Deal detection: compare listing prices against benchmarks and auto-computed medians."""

import logging
from statistics import median

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Listing, PriceBenchmark

logger = logging.getLogger(__name__)
settings = get_settings()


def detect_deal(db: Session, listing: Listing) -> None:
    """Check if a single listing qualifies as a deal and update it."""
    if listing.price is None:
        return

    benchmark_price = _find_benchmark_price(db, listing)
    if benchmark_price is None:
        benchmark_price = _compute_auto_median(db, listing)

    if benchmark_price is None:
        return

    savings = float(benchmark_price) - float(listing.price)
    if savings >= settings.DEAL_THRESHOLD:
        listing.is_deal = True
        listing.deal_savings = savings
    else:
        listing.is_deal = False
        listing.deal_savings = None


def detect_deals_all(db: Session) -> int:
    """Re-run deal detection for all active listings. Returns count of deals found."""
    listings = db.query(Listing).filter(Listing.is_archived == False).all()
    deals_found = 0

    for listing in listings:
        detect_deal(db, listing)
        if listing.is_deal:
            deals_found += 1

    db.commit()
    logger.info("Deal detection complete: %d deals found out of %d listings", deals_found, len(listings))
    return deals_found


def _find_benchmark_price(db: Session, listing: Listing) -> float | None:
    """Find the most specific manual benchmark matching this listing.

    Specificity = count of non-null matching fields. Higher is more specific.
    """
    benchmarks = db.query(PriceBenchmark).all()
    best_match = None
    best_specificity = -1

    for bench in benchmarks:
        specificity = 0
        matches = True

        if bench.vehicle_type is not None:
            if listing.vehicle_type and listing.vehicle_type.lower() == bench.vehicle_type.lower():
                specificity += 1
            else:
                matches = False
                continue

        if bench.make is not None:
            if listing.make and listing.make.lower() == bench.make.lower():
                specificity += 1
            else:
                matches = False
                continue

        if bench.model is not None:
            if listing.model and listing.model.lower() == bench.model.lower():
                specificity += 1
            else:
                matches = False
                continue

        if bench.year_min is not None or bench.year_max is not None:
            if listing.year is None:
                matches = False
                continue
            if bench.year_min is not None and listing.year < bench.year_min:
                matches = False
                continue
            if bench.year_max is not None and listing.year > bench.year_max:
                matches = False
                continue
            specificity += 1

        if bench.mileage_min is not None or bench.mileage_max is not None:
            if listing.mileage is None:
                matches = False
                continue
            if bench.mileage_min is not None and listing.mileage < bench.mileage_min:
                matches = False
                continue
            if bench.mileage_max is not None and listing.mileage > bench.mileage_max:
                matches = False
                continue
            specificity += 1

        if matches and specificity > best_specificity:
            best_specificity = specificity
            best_match = bench

    if best_match:
        return float(best_match.benchmark_price)
    return None


def _compute_auto_median(db: Session, listing: Listing) -> float | None:
    """Compute median price from similar active listings.

    Groups by: vehicle_type + make + model + year_bucket (5yr) + mileage_bucket (100k).
    Requires >= 5 data points.
    """
    if not listing.vehicle_type or not listing.make or not listing.model:
        return None

    query = db.query(Listing.price).filter(
        Listing.is_archived == False,
        Listing.price.isnot(None),
        Listing.vehicle_type == listing.vehicle_type,
        Listing.make == listing.make,
        Listing.model == listing.model,
    )

    # Year bucket (5-year range)
    if listing.year is not None:
        year_bucket_start = (listing.year // 5) * 5
        query = query.filter(
            Listing.year >= year_bucket_start,
            Listing.year < year_bucket_start + 5,
        )

    # Mileage bucket (100k range)
    if listing.mileage is not None:
        mileage_bucket_start = (listing.mileage // 100000) * 100000
        query = query.filter(
            Listing.mileage >= mileage_bucket_start,
            Listing.mileage < mileage_bucket_start + 100000,
        )

    prices = [float(row[0]) for row in query.all()]

    if len(prices) < 5:
        return None

    return median(prices)
