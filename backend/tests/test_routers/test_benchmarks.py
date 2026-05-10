"""Tests for benchmarks CRUD API endpoints."""

import pytest


class TestBenchmarksCRUD:
    def test_create(self, client):
        r = client.post("/api/benchmarks", json={
            "vehicle_type": "truck",
            "make": "Freightliner",
            "model": "Cascadia",
            "benchmark_price": 80000,
        })
        assert r.status_code == 201
        data = r.json()
        assert data["make"] == "Freightliner"
        assert data["benchmark_price"] == 80000
        assert data["id"] is not None

    def test_list(self, client, db, sample_benchmark):
        r = client.get("/api/benchmarks")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_update(self, client, db, sample_benchmark):
        r = client.put(f"/api/benchmarks/{sample_benchmark.id}", json={
            "benchmark_price": 85000,
        })
        assert r.status_code == 200
        assert r.json()["benchmark_price"] == 85000

    def test_delete(self, client, db, sample_benchmark):
        r = client.delete(f"/api/benchmarks/{sample_benchmark.id}")
        assert r.status_code == 204

        r = client.get("/api/benchmarks")
        assert len(r.json()) == 0

    def test_update_not_found(self, client):
        r = client.put("/api/benchmarks/99999", json={"benchmark_price": 50000})
        assert r.status_code == 404

    def test_delete_not_found(self, client):
        r = client.delete("/api/benchmarks/99999")
        assert r.status_code == 404
