"""Tests for deals API endpoints."""

import pytest


class TestListDeals:
    def test_empty(self, client):
        r = client.get("/api/deals")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_returns_deals_only(self, client, db, sample_listing):
        r = client.get("/api/deals")
        assert r.json()["total"] == 0  # sample_listing.is_deal defaults to False

        sample_listing.is_deal = True
        sample_listing.deal_savings = 15000
        db.commit()

        r = client.get("/api/deals")
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["deal_savings"] == 15000
