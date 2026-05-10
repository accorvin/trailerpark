"""Tests for duplicate detection."""

import pytest
from src.models import Email, Listing
from src.services.deduplicator import check_duplicate, deduplicate_listing


class TestCheckDuplicate:
    def test_detects_exact_duplicate(self, db, sample_listing, sample_email):
        dup = Listing(
            email_id=sample_email.id, vehicle_type="truck",
            make="Freightliner", model="Cascadia", year=2022,
            mileage=348000, price=64000,  # within 5% mileage, 10% price
        )
        db.add(dup)
        db.commit()
        db.refresh(dup)

        result = check_duplicate(db, dup)
        assert result is not None
        assert result.id == sample_listing.id

    def test_no_duplicate_different_model(self, db, sample_listing, sample_email):
        different = Listing(
            email_id=sample_email.id, vehicle_type="truck",
            make="Freightliner", model="Columbia", year=2022,
            mileage=350000, price=65000,
        )
        db.add(different)
        db.commit()
        db.refresh(different)

        result = check_duplicate(db, different)
        assert result is None

    def test_no_duplicate_price_too_different(self, db, sample_listing, sample_email):
        different = Listing(
            email_id=sample_email.id, vehicle_type="truck",
            make="Freightliner", model="Cascadia", year=2022,
            mileage=350000, price=85000,  # >10% price difference
        )
        db.add(different)
        db.commit()
        db.refresh(different)

        result = check_duplicate(db, different)
        assert result is None


class TestDeduplicateListing:
    def test_removes_duplicate(self, db, sample_listing, sample_email):
        dup = Listing(
            email_id=sample_email.id, vehicle_type="truck",
            make="Freightliner", model="Cascadia", year=2022,
            mileage=348000, price=64000,
        )
        db.add(dup)
        db.commit()
        db.refresh(dup)

        was_dup = deduplicate_listing(db, dup)
        assert was_dup is True

        # Dup should be deleted
        assert db.get(Listing, dup.id) is None
        # Original should still exist with updated last_seen_at
        db.refresh(sample_listing)
        assert sample_listing.last_seen_at is not None
