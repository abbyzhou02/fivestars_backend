from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .evidence_extractor import extract_covered_facets_from_draft
from .models import AmenitySnapshot
from .settings import settings
from .taxonomy import FACET_CONFIG



PRIORITY_BOOSTS = {
    ("ROOM_INFRA", "wifi_fee"): 0.25,
    ("ROOM_SERVICE", "breakfast_included"): 0.25,
    ("PARKING", "included"): 0.22,
    ("HOTEL_INFRA", "shuttle"): 0.22,
    ("ROOM_CLEANLINESS", "surfaces_clean"): 0.20,
    ("ROOM_CLEANLINESS", "odor"): 0.20,
    ("NOISE", "external_noise"): 0.18,
    ("ROOM_INFRA", "hvac_working"): 0.18,
}

# ---------------------------------------------------
# Candidate
# ---------------------------------------------------

@dataclass
class Candidate:
    property_id: str
    amenity_id: str
    facet: str
    state: str
    score: float
    question_text: str
    options: list[dict[str, str]]
    debug: dict[str, Any]


# ---------------------------------------------------
# fatigue penalty
# ---------------------------------------------------

def _fatigue_penalty(asked_facets: list[tuple[str, str]]) -> float:
    return 0.15 * len(asked_facets)


# ---------------------------------------------------
# official fact boost
# ---------------------------------------------------

def _official_boost(snapshot: AmenitySnapshot, amenity_listed: bool) -> float:

    boost = 0.0

    if snapshot.official_fact != "not_listed":
        boost += 0.10

    if amenity_listed:
        boost += 0.08

    if snapshot.facet == "availability" and snapshot.official_fact != "not_listed":
        boost += 0.15

    if snapshot.state == "STALE" and snapshot.facet == "availability":
        boost += 0.15

    if snapshot.official_fact == "seasonal":
        boost += 0.05

    return boost


# ---------------------------------------------------
# state bonus
# ---------------------------------------------------

def _state_bonus(state: str) -> float:

    return {
        "CONFLICT": 0.20,
        "STALE": 0.10,
        "MISSING": 0.05,
        "SATURATED": -0.25,
    }.get(state, 0.0)


# ---------------------------------------------------
# score
# ---------------------------------------------------

def _score(snapshot: AmenitySnapshot, amenity_listed: bool, asked_facets: list[tuple[str, str]]) -> float:

    cfg = FACET_CONFIG[(snapshot.amenity_id, snapshot.facet)]

    official_boost = _official_boost(snapshot, amenity_listed)

    fatigue = _fatigue_penalty(asked_facets)

    priority = PRIORITY_BOOSTS.get((snapshot.amenity_id, snapshot.facet), 0)

    score = cfg.answerability * (

        0.40 * snapshot.coverage_gap
        + 0.30 * snapshot.staleness_score
        + 0.30 * snapshot.conflict_score
        + 0.20 * cfg.business_importance
        + official_boost
        + priority
        - fatigue
    ) + _state_bonus(snapshot.state)

    # ---------------------------------------------------
    # rules
    # ---------------------------------------------------

    # availability 未稳定 → 不问 quality
    if snapshot.facet == "quality":
        score -= 0.10

    # 避免问 saturated
    if snapshot.state == "SATURATED":
        score -= 0.30

    # availability stale/conflict 强推
    if (
        snapshot.facet == "availability"
        and snapshot.official_fact != "not_listed"
        and snapshot.state in {"STALE", "CONFLICT"}
    ):
        score += 0.15

    # WiFi：如果 availability 已知 → 问 reliability
    if snapshot.amenity_id == "WIFI" and snapshot.facet == "availability":
        score -= 0.15

    # 非官方 amenity 的 stale
    if snapshot.state == "STALE" and snapshot.official_fact == "not_listed":
        score -= 0.10

    return round(score, 4)


# ---------------------------------------------------
# pick followup
# ---------------------------------------------------

def pick_followup(
    db: Session,
    property_id: str,
    draft_text: str,
    asked_facets: list[tuple[str, str]] | None = None,
    stay_date: date | None = None,
) -> Candidate | None:

    asked_facets = asked_facets or []

    covered = extract_covered_facets_from_draft(draft_text)

    rows = db.execute(
        select(AmenitySnapshot).where(AmenitySnapshot.property_id == property_id)
    ).scalars().all()

    if not rows:
        return None

    amenity_listed_map = {}

    for row in rows:
        if row.facet == "availability":
            amenity_listed_map[row.amenity_id] = row.official_fact != "not_listed"

    candidates: list[Candidate] = []

    for row in rows:

        key = (row.amenity_id, row.facet)

        if key in covered or key in asked_facets:
            continue

        cfg = FACET_CONFIG.get(key)

        if cfg is None:
            continue

        score = _score(row, amenity_listed_map.get(row.amenity_id, False), asked_facets)

        debug = {
            "state": row.state,
            "official_fact": row.official_fact,
            "coverage_gap": row.coverage_gap,
            "staleness_score": row.staleness_score,
            "conflict_score": row.conflict_score,
            "actual_recent_coverage": row.actual_recent_coverage,
            "expected_recent_coverage": row.expected_recent_coverage,
            "lifetime_coverage": row.lifetime_coverage,
            "last_verified_at": str(row.last_verified_at) if row.last_verified_at else None,
            "stay_date": str(stay_date) if stay_date else None,
        }

        candidates.append(
            Candidate(
                property_id=property_id,
                amenity_id=row.amenity_id,
                facet=row.facet,
                state=row.state,
                score=score,
                question_text=cfg.question_text,
                options=cfg.options,
                debug=debug,
            )
        )

    if not candidates:
        return None

    candidates.sort(key=lambda x: x.score, reverse=True)

    best = candidates[0]

    if best.score < settings.ask_threshold:
        return None

    return best


# ---------------------------------------------------
# top candidates
# ---------------------------------------------------

def top_candidates(
    db: Session,
    property_id: str,
    draft_text: str,
    asked_facets: list[tuple[str, str]] | None = None,
    limit: int = 5,
) -> list[Candidate]:

    asked_facets = asked_facets or []

    covered = extract_covered_facets_from_draft(draft_text)

    rows = db.execute(
        select(AmenitySnapshot).where(AmenitySnapshot.property_id == property_id)
    ).scalars().all()

    amenity_listed_map = {}

    for row in rows:
        if row.facet == "availability":
            amenity_listed_map[row.amenity_id] = row.official_fact != "not_listed"

    candidates: list[Candidate] = []

    for row in rows:

        key = (row.amenity_id, row.facet)

        if key in covered or key in asked_facets:
            continue

        cfg = FACET_CONFIG.get(key)

        if cfg is None:
            continue

        candidates.append(
            Candidate(
                property_id=property_id,
                amenity_id=row.amenity_id,
                facet=row.facet,
                state=row.state,
                score=_score(row, amenity_listed_map.get(row.amenity_id, False), asked_facets),
                question_text=cfg.question_text,
                options=cfg.options,
                debug={
                    "official_fact": row.official_fact,
                    "coverage_gap": row.coverage_gap,
                    "staleness_score": row.staleness_score,
                    "conflict_score": row.conflict_score,
                    "actual_recent_coverage": row.actual_recent_coverage,
                    "expected_recent_coverage": row.expected_recent_coverage,
                    "lifetime_coverage": row.lifetime_coverage,
                    "last_verified_at": str(row.last_verified_at) if row.last_verified_at else None,
                },
            )
        )

    candidates.sort(key=lambda x: x.score, reverse=True)

    return candidates[:limit]