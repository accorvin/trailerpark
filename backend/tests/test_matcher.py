"""Tests for buyer-seller matching."""

import pytest
from src.models import BuyerRequest, Listing
from src.services.matcher import score_match, match_all


class TestScoreMatch:
    def test_full_match(self, sample_listing, sample_buyer):
        score = score_match(sample_buyer, sample_listing)
        # vehicle_type required (pass) + make(0.15) + model(0.25) + year(0.2) + mileage(0.15) + price(0.2)
        assert score == pytest.approx(0.95, abs=0.01)

    def test_vehicle_type_mismatch_zero(self, sample_listing, sample_buyer):
        sample_buyer.vehicle_type = "trailer"
        score = score_match(sample_buyer, sample_listing)
        assert score == 0.0

    def test_partial_match(self, db, sample_email, sample_buyer):
        # Different make/model but same vehicle type
        listing = Listing(
            email_id=sample_email.id, vehicle_type="truck",
            make="Peterbilt", model="579", year=2022,
            mileage=300000, price=60000,
        )
        db.add(listing)
        db.commit()

        score = score_match(sample_buyer, listing)
        # vehicle_type match + year in range(0.2) + mileage(0.15) + price(0.2) = 0.55
        assert score == pytest.approx(0.55, abs=0.01)

    def test_below_threshold_not_stored(self, db, sample_listing, sample_buyer):
        sample_buyer.vehicle_type = "trailer"
        db.commit()
        count = match_all(db)
        assert count == 0


class TestMatchAll:
    def test_creates_matches(self, db, sample_listing, sample_buyer):
        count = match_all(db)
        assert count == 1

    def test_clears_old_matches(self, db, sample_listing, sample_buyer):
        match_all(db)
        # Run again — should clear and recreate
        count = match_all(db)
        assert count == 1
