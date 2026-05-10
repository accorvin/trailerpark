"""Benchmarks CRUD API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PriceBenchmark
from ..schemas import BenchmarkCreate, BenchmarkResponse, BenchmarkUpdate

router = APIRouter(tags=["benchmarks"])


@router.get("/benchmarks", response_model=list[BenchmarkResponse])
def list_benchmarks(db: Session = Depends(get_db)):
    return db.query(PriceBenchmark).order_by(PriceBenchmark.created_at.desc()).all()


@router.post("/benchmarks", response_model=BenchmarkResponse, status_code=201)
def create_benchmark(data: BenchmarkCreate, db: Session = Depends(get_db)):
    benchmark = PriceBenchmark(**data.model_dump())
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)
    return benchmark


@router.put("/benchmarks/{benchmark_id}", response_model=BenchmarkResponse)
def update_benchmark(
    benchmark_id: int,
    data: BenchmarkUpdate,
    db: Session = Depends(get_db),
):
    benchmark = db.get(PriceBenchmark, benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(benchmark, key, value)

    db.commit()
    db.refresh(benchmark)
    return benchmark


@router.delete("/benchmarks/{benchmark_id}", status_code=204)
def delete_benchmark(benchmark_id: int, db: Session = Depends(get_db)):
    benchmark = db.get(PriceBenchmark, benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    db.delete(benchmark)
    db.commit()
