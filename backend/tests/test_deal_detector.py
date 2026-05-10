"""Tests for deal detection logic."""

import pytest
from src.models import Listing, PriceBenchmark
from src.services.deal_detector import detect_deal, _find_benchmark_price, _compute_auto_median


class TestFindBenchmarkPrice:
    def test_exact_match(self, db, sample_listing, sample_benchmark):
        price = _find_benchmark_price(db, sample_listing)
        assert price == 80000

    def test_no_match(self, db, sample_listing):
        result = _find_benchmark_price(db, sample_listing)
        assert result is None

    def test_most_specific_wins(self, db, sample_listing):
        # Generic benchmark
        bench1 = PriceBenchmark(vehicle_type="truck", benchmark_price=90000)
        # Specific benchmark
        bench2 = PriceBenchmark(
            vehicle_type="truck", make="Freightliner", model="Cascadia",
            year_min=2020, year_max=2025, benchmark_price=80000,
        )
        db.add_all([bench1, bench2])
        db.commit()

        price = _find_benchmark_price(db, sample_listing)
        assert price == 80000  # more specific benchmark wins


class TestDetectDeal:
    def test_deal_detected(self, db, sample_listing, sample_benchmark):
        # listing price=65000, benchmark=80000, savings=15000 >= threshold(10000)
        detect_deal(db, sample_listing)
        assert sample_listing.is_deal is True
        assert sample_listing.deal_savings == 15000

    def test_no_deal_below_threshold(self, db, sample_listing):
        bench = PriceBenchmark(
            vehicle_type="truck", make="Freightliner", model="Cascadia",
            year_min=2020, year_max=2025, benchmark_price=70000,
        )
        db.add(bench)
        db.commit()
        # savings = 70000 - 65000 = 5000 < 10000 threshold
        detect_deal(db, sample_listing)
        assert sample_listing.is_deal is False

    def test_null_price_skipped(self, db, sample_email):
        listing = Listing(
            email_id=sample_email.id, vehicle_type="truck",
            make="Freightliner", model="Cascadia",
            year=2022, price=None,
        )
        db.add(listing)
        db.commit()

        detect_deal(db, listing)
        assert listing.is_deal is False
