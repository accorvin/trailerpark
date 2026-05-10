"""Tests for auto-archive logic."""

from datetime import datetime, timedelta

import pytest
from src.models import Email, Listing, BuyerRequest
from src.services.archiver import archive_old


class TestArchiver:
    def test_archives_old_listings(self, db):
        email = Email(id="old/old-email", classification="seller_listing")
        db.add(email)
        db.flush()

        listing = Listing(
            email_id=email.id, vehicle_type="truck",
            make="Test", model="Test", year=2020,
            first_seen_at=datetime.now() - timedelta(days=25),
        )
        db.add(listing)
        db.commit()

        archived = archive_old(db)
        assert archived == 1

        db.refresh(listing)
        assert listing.is_archived is True
        assert listing.archived_at is not None

    def test_does_not_archive_recent(self, db, sample_listing):
        archived = archive_old(db)
        assert archived == 0
        db.refresh(sample_listing)
        assert sample_listing.is_archived is False

    def test_archives_old_buyer_requests(self, db):
        email = Email(id="old/buyer-email", classification="buyer_request")
        db.add(email)
        db.flush()

        buyer = BuyerRequest(
            email_id=email.id, vehicle_type="truck",
            first_seen_at=datetime.now() - timedelta(days=25),
        )
        db.add(buyer)
        db.commit()

        archived = archive_old(db)
        assert archived == 1
        db.refresh(buyer)
        assert buyer.is_archived is True
