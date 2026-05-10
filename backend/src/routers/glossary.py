"""Glossary API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import GlossaryEntry
from ..schemas import GlossaryEntryCreate, GlossaryEntryResponse, GlossaryEntryUpdate, PaginatedResponse, SeedResponse
from ..services.glossary import invalidate_glossary_cache, seed_glossary

router = APIRouter(tags=["glossary"])


@router.get("/glossary", response_model=PaginatedResponse)
def list_glossary(
    category: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(GlossaryEntry).filter(GlossaryEntry.is_deleted == False)

    if category:
        query = query.filter(GlossaryEntry.category == category)
    if search:
        query = query.filter(
            (GlossaryEntry.abbreviation.ilike(f"%{search}%"))
            | (GlossaryEntry.expansion.ilike(f"%{search}%"))
        )

    total = query.count()
    pages = (total + per_page - 1) // per_page
    items = (
        query.order_by(GlossaryEntry.usage_count.desc(), GlossaryEntry.abbreviation)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedResponse(
        items=[GlossaryEntryResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.post("/glossary", response_model=GlossaryEntryResponse, status_code=201)
def create_glossary_entry(data: GlossaryEntryCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(GlossaryEntry)
        .filter(GlossaryEntry.abbreviation == data.abbreviation)
        .first()
    )
    if existing:
        if existing.is_deleted:
            # Restore tombstoned entry with new data
            existing.expansion = data.expansion
            existing.category = data.category
            existing.source = "user"
            existing.is_deleted = False
            db.commit()
            db.refresh(existing)
            invalidate_glossary_cache()
            return existing
        raise HTTPException(status_code=409, detail="Abbreviation already exists")

    entry = GlossaryEntry(
        abbreviation=data.abbreviation,
        expansion=data.expansion,
        category=data.category,
        source="user",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    invalidate_glossary_cache()
    return entry


@router.put("/glossary/{entry_id}", response_model=GlossaryEntryResponse)
def update_glossary_entry(entry_id: int, data: GlossaryEntryUpdate, db: Session = Depends(get_db)):
    entry = db.get(GlossaryEntry, entry_id)
    if not entry or entry.is_deleted:
        raise HTTPException(status_code=404, detail="Glossary entry not found")

    if data.abbreviation is not None:
        entry.abbreviation = data.abbreviation
    if data.expansion is not None:
        entry.expansion = data.expansion
    if data.category is not None:
        entry.category = data.category
    entry.source = "user"  # User edit always sets source to user

    db.commit()
    db.refresh(entry)
    invalidate_glossary_cache()
    return entry


@router.delete("/glossary/{entry_id}", status_code=204)
def delete_glossary_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(GlossaryEntry, entry_id)
    if not entry or entry.is_deleted:
        raise HTTPException(status_code=404, detail="Glossary entry not found")

    entry.is_deleted = True
    db.commit()
    invalidate_glossary_cache()


@router.post("/glossary/seed", response_model=SeedResponse)
def seed_glossary_entries(db: Session = Depends(get_db)):
    added = seed_glossary(db)
    return {"added": added, "message": f"Seeded {added} new glossary entries"}
