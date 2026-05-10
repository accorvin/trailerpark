"""Tests for matches API endpoints."""

import pytest
from src.models import Match


class TestListMatches:
    def test_empty(self, client):
        r = client.get("/api/matches")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_returns_matches(self, client, db, sample_listing, sample_buyer):
        match = Match(
            buyer_request_id=sample_buyer.id,
            listing_id=sample_listing.id,
            score=0.85,
        )
        db.add(match)
        db.commit()

        r = client.get("/api/matches")
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["score"] == 0.85
