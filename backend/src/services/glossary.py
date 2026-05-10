"""Glossary service for jargon abbreviation management."""

import logging
import time

from sqlalchemy.orm import Session

from ..models import GlossaryEntry

logger = logging.getLogger(__name__)

# Module-level cache
_glossary_cache: str | None = None
_glossary_cache_time: float = 0
GLOSSARY_CACHE_TTL = 300  # 5 minutes

# Fields eligible for auto-learning
AUTO_LEARN_FIELDS = {"make", "model", "engine_type", "vehicle_type"}


def get_glossary_prompt_section(db: Session) -> str:
    """Build a formatted glossary string for injection into LLM system prompts.

    Cached for 5 minutes. Capped at top 200 entries by usage_count.
    """
    global _glossary_cache, _glossary_cache_time

    now = time.time()
    if _glossary_cache is not None and (now - _glossary_cache_time) < GLOSSARY_CACHE_TTL:
        return _glossary_cache

    entries = (
        db.query(GlossaryEntry)
        .filter(GlossaryEntry.is_deleted == False)
        .order_by(GlossaryEntry.usage_count.desc())
        .limit(200)
        .all()
    )

    if not entries:
        _glossary_cache = ""
        _glossary_cache_time = now
        return ""

    # Group by category
    by_category: dict[str | None, list[GlossaryEntry]] = {}
    for entry in entries:
        by_category.setdefault(entry.category, []).append(entry)

    lines = [
        "\n## Industry Abbreviations Reference",
        "The following abbreviations are commonly used in commercial trucking emails:",
    ]
    for category, items in sorted(by_category.items(), key=lambda x: x[0] or "zzz"):
        if category:
            lines.append(f"\n### {category.replace('_', ' ').title()}")
        for item in items:
            # Sanitize: strip newlines, truncate to prevent prompt injection
            abbr = item.abbreviation.replace("\n", " ").replace("\r", " ")[:20]
            exp = item.expansion.replace("\n", " ").replace("\r", " ")[:200]
            lines.append(f"- {abbr} = {exp}")

    lines.append("\nWhen you encounter these abbreviations, use the full expanded form in your output.")

    result = "\n".join(lines)
    _glossary_cache = result
    _glossary_cache_time = now
    return result


def invalidate_glossary_cache():
    """Called after any glossary CRUD operation to bust the cache."""
    global _glossary_cache, _glossary_cache_time
    _glossary_cache = None
    _glossary_cache_time = 0


def record_abbreviation_match(db: Session, abbreviation: str):
    """Increment usage_count when an abbreviation is found in processed email text."""
    entry = (
        db.query(GlossaryEntry)
        .filter(GlossaryEntry.abbreviation == abbreviation, GlossaryEntry.is_deleted == False)
        .first()
    )
    if entry:
        entry.usage_count = (entry.usage_count or 0) + 1


def scan_and_record_matches(db: Session, text: str):
    """Scan email text for glossary abbreviations and increment their usage counts.

    Uses word-boundary matching to avoid false positives (e.g. "FRL" inside "UNFRL").
    """
    import re

    if not text:
        return

    entries = (
        db.query(GlossaryEntry)
        .filter(GlossaryEntry.is_deleted == False)
        .all()
    )
    if not entries:
        return

    for entry in entries:
        # Use word-boundary regex for accurate matching (case-insensitive)
        pattern = re.compile(r'\b' + re.escape(entry.abbreviation) + r'\b', re.IGNORECASE)
        if pattern.search(text):
            entry.usage_count = (entry.usage_count or 0) + 1


def auto_learn_entry(db: Session, abbreviation: str, expansion: str, category: str | None = None):
    """Create or update a glossary entry from a user correction (source='auto_learned').

    Priority: user > auto_learned > seed.
    """
    normalized = abbreviation.upper().strip()
    existing = (
        db.query(GlossaryEntry)
        .filter(GlossaryEntry.abbreviation == normalized)
        .first()
    )

    if existing:
        if existing.is_deleted:
            # User deleted this — don't re-add via auto-learn
            return
        if existing.source == "user":
            # Never override user entries
            return
        # Override seed entries; update auto_learned entries
        existing.expansion = expansion
        existing.source = "auto_learned"
        if category:
            existing.category = category
    else:
        entry = GlossaryEntry(
            abbreviation=normalized,
            expansion=expansion,
            category=category,
            source="auto_learned",
        )
        db.add(entry)

    invalidate_glossary_cache()


def is_abbreviation_correction(field_name: str, original: str | None, corrected: str | None) -> bool:
    """Detect if a field correction looks like an abbreviation expansion."""
    if field_name not in AUTO_LEARN_FIELDS:
        return False
    if not original or not corrected:
        return False
    original = original.strip()
    corrected = corrected.strip()
    if not (2 <= len(original) <= 5):
        return False
    if not original.isupper():
        return False
    if len(corrected) < len(original) * 2:
        return False
    # Don't auto-learn if abbreviation already exists as user entry
    return True


def seed_glossary(db: Session) -> int:
    """Seed default glossary entries. Skips existing and tombstoned abbreviations."""
    from .glossary_seed import SEED_DATA

    added = 0
    for item in SEED_DATA:
        existing = (
            db.query(GlossaryEntry)
            .filter(GlossaryEntry.abbreviation == item["abbreviation"])
            .first()
        )
        if existing:
            continue  # Skip existing (including tombstoned)
        entry = GlossaryEntry(
            abbreviation=item["abbreviation"],
            expansion=item["expansion"],
            category=item.get("category"),
            source="seed",
        )
        db.add(entry)
        added += 1

    if added:
        db.commit()
        invalidate_glossary_cache()

    return added
