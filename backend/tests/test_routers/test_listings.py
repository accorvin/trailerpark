"""Tests for listings API endpoints."""

import pytest
from src.models import Email, Listing


class TestListListings:
    def test_empty(self, client):
        r = client.get("/api/listings")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_returns_active_listings(self, client, db, sample_listing):
        r = client.get("/api/listings")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["make"] == "Freightliner"

    def test_excludes_archived(self, client, db, sample_listing):
        sample_listing.is_archived = True
        db.commit()
        r = client.get("/api/listings")
        assert r.json()["total"] == 0

    def test_filter_by_make(self, client, db, sample_listing):
        r = client.get("/api/listings?make=Freightliner")
        assert r.json()["total"] == 1
        r = client.get("/api/listings?make=Peterbilt")
        assert r.json()["total"] == 0

    def test_filter_by_year_range(self, client, db, sample_listing):
        r = client.get("/api/listings?year_min=2020&year_max=2025")
        assert r.json()["total"] == 1
        r = client.get("/api/listings?year_min=2023")
        assert r.json()["total"] == 0

    def test_pagination(self, client, db, sample_listing):
        r = client.get("/api/listings?page=1&per_page=1")
        data = r.json()
        assert data["page"] == 1
        assert data["per_page"] == 1


class TestGetListing:
    def test_found(self, client, db, sample_listing):
        r = client.get(f"/api/listings/{sample_listing.id}")
        assert r.status_code == 200
        assert r.json()["make"] == "Freightliner"

    def test_not_found(self, client):
        r = client.get("/api/listings/99999")
        assert r.status_code == 404


class TestArchive:
    def test_returns_archived(self, client, db, sample_listing):
        sample_listing.is_archived = True
        db.commit()
        r = client.get("/api/archive")
        assert r.json()["total"] == 1
