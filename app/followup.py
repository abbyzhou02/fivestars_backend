from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AmenitySnapshot
from .settings import settings
from .taxonomy import FACET_CONFIG


@dataclass(frozen=True)
class FollowupCandidate:
    property_id: str
    amenity_id: str
    facet: str
    state: str
    score: float
    question_text: str
    options: list[dict[str, str]]
    debug: dict[str, Any]


def _facet_key(amenity_id: str, facet: str) -> str:
    return f"{amenity_id}:{facet}"


def _normalize_asked_facets(asked_facets: Iterable[Any] | None) -> set[str]:
    normalized: set[str] = set()
    if not asked_facets:
        return normalized

    for item in asked_facets:
        amenity_id: str | None = None
        facet: str | None = None

        if isinstance(item, str):
            for separator in (":", ".", "/", "|"):
                if separator in item:
                    left, right = item.split(separator, 1)
                    amenity_id, facet = left.strip(), right.strip()
                    break
        elif isinstance(item, dict):
            amenity_id = item.get("amenity_id")
            facet = item.get("facet")
        elif isinstance(item, (tuple, list)) and len(item) == 2:
            amenity_id = str(item[0])
            facet = str(item[1])

        if amenity_id and facet:
            normalized.add(_facet_key(amenity_id, facet))

    return normalized


def _draft_penalty(draft_text: str | None, amenity_id: str, facet: str) -> float:
    if not draft_text:
        return 0.0

    draft = draft_text.lower()
    keyword_map = {
        ("PARKING", "included"): ["parking", "park"],
        ("PARKING", "entrance_findability"): ["parking entrance"],
        ("ROOM_CLEANLINESS", "surfaces_clean"): ["clean", "dirty", "dusty"],
        ("ROOM_CLEANLINESS", "bedding_clean"): ["sheet", "bedding", "bed linen"],
        ("ROOM_CLEANLINESS", "odor"): ["smell", "odor", "musty", "smoke"],
        ("ROOM_INFRA", "wifi_available"): ["wifi", "wi-fi", "internet"],
        ("ROOM_INFRA", "wifi_fee"): ["wifi", "wi-fi", "internet"],
        ("ROOM_SERVICE", "breakfast_included"): ["breakfast"],
        ("HOTEL_INFRA", "shuttle"): ["shuttle"],
        ("NOISE", "external_noise"): ["noise", "quiet", "hallway", "street noise"],
    }

    keywords = keyword_map.get((amenity_id, facet), [])
    if keywords and any(keyword in draft for keyword in keywords):
        return 0.12
    return 0.0


def _score_snapshot(snapshot: AmenitySnapshot) -> FollowupCandidate | None:
    cfg = FACET_CONFIG.get((snapshot.amenity_id, snapshot.facet))
    if cfg is None:
        return None

    state_bonus = {
        "CONFLICT": 0.22,
        "STALE": 0.12,
        "MISSING": 0.05,
        "SATURATED": -0.20,
    }.get(snapshot.state, 0.0)

    raw_score = (
        0.35 * snapshot.coverage_gap
        + 0.25 * snapshot.staleness_score
        + 0.30 * snapshot.conflict_score
        + 0.07 * cfg.business_importance
        + 0.03 * cfg.answerability
        + state_bonus
    )

    score = round(max(0.0, min(1.0, raw_score)), 3)

    return FollowupCandidate(
        property_id=snapshot.property_id,
        amenity_id=snapshot.amenity_id,
        facet=snapshot.facet,
        state=snapshot.state,
        score=score,
        question_text=cfg.question_text,
        options=cfg.options,
        debug={
            "coverage_gap": snapshot.coverage_gap,
            "staleness_score": snapshot.staleness_score,
            "conflict_score": snapshot.conflict_score,
            "business_importance": cfg.business_importance,
            "answerability": cfg.answerability,
            "state_bonus": state_bonus,
            "official_fact": snapshot.official_fact,
        },
    )


def top_candidates(
    db: Session,
    property_id: str,
    draft_text: str | None = None,
    asked_facets: list[Any] | None = None,
    limit: int = 5,
) -> list[FollowupCandidate]:
    asked = _normalize_asked_facets(asked_facets)
    snapshots = db.execute(
        select(AmenitySnapshot)
        .where(AmenitySnapshot.property_id == property_id)
        .order_by(AmenitySnapshot.amenity_id, AmenitySnapshot.facet)
    ).scalars().all()

    ranked: list[FollowupCandidate] = []
    for snapshot in snapshots:
        if _facet_key(snapshot.amenity_id, snapshot.facet) in asked:
            continue
        if snapshot.state == "SATURATED" and snapshot.conflict_score < 0.2:
            continue

        candidate = _score_snapshot(snapshot)
        if candidate is None:
            continue

        penalty = _draft_penalty(draft_text, snapshot.amenity_id, snapshot.facet)
        adjusted_score = round(max(0.0, candidate.score - penalty), 3)
        ranked.append(
            FollowupCandidate(
                property_id=candidate.property_id,
                amenity_id=candidate.amenity_id,
                facet=candidate.facet,
                state=candidate.state,
                score=adjusted_score,
                question_text=candidate.question_text,
                options=candidate.options,
                debug={**candidate.debug, "draft_penalty": penalty},
            )
        )

    ranked.sort(key=lambda item: (-item.score, item.amenity_id, item.facet))
    return ranked[:limit]


def pick_followup(
    db: Session,
    property_id: str,
    draft_text: str | None = None,
    asked_facets: list[Any] | None = None,
    stay_date: date | None = None,
) -> FollowupCandidate | None:
    _ = stay_date  # reserved for future use
    candidates = top_candidates(
        db=db,
        property_id=property_id,
        draft_text=draft_text,
        asked_facets=asked_facets,
        limit=1,
    )
    if not candidates:
        return None

    candidate = candidates[0]
    if candidate.score < settings.ask_threshold:
        return None
    return candidate
