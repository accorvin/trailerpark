"""Matches API endpoints."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Match
from ..schemas import MatchResponse, PaginatedResponse

router = APIRouter(tags=["matches"])


class RunResponse(BaseModel):
    message: str


@router.post("/matches/run", response_model=RunResponse)
def run_matching(db: Session = Depends(get_db)):
    """Manually trigger buyer-seller matching."""
    from ..services.matcher import match_all

    matches_found = match_all(db)
    return RunResponse(message=f"Matching complete: {matches_found} match(es) found")


@router.get("/matches", response_model=PaginatedResponse)
def list_matches(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Match)
        .options(joinedload(Match.buyer_request), joinedload(Match.listing))
    )
    total = db.query(Match).count()
    pages = (total + per_page - 1) // per_page
    items = (
        query.order_by(Match.score.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedResponse(
        items=[MatchResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )
