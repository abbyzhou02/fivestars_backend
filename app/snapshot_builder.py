from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .models import AmenitySnapshot, OfficialFact, Property, Review, ReviewEvidence
from .settings import settings
from .taxonomy import AMENITY_FACETS, FACET_CONFIG


def lag_aware_today(as_of: date | None = None) -> date:
    base_date = as_of or date.today()
    return base_date - timedelta(days=settings.pending_review_lag_days)


def normalize_expected_rate(raw_rate: float) -> float:
    """
    Backward-compatible normalization.

    Old taxonomy values used 1 / 2 to mean 1% / 2%.
    New taxonomy values can use 0.01 / 0.02 directly.
    """
    rate = max(float(raw_rate), 0.0)
    if rate >= 1.0:
        return rate / 100.0
    return rate


def contradiction_score(official_fact: str, pos: int, neg: int) -> float:
    total = pos + neg
    if total == 0:
        return 0.0

    positive_official = {"listed", "included", "open", "seasonal", "yes", "available", "working"}
    negative_official = {"not_listed", "surcharge", "temporarily_closed", "surcharge_or_limited", "no", "not_available"}

    base = min(pos, neg) / total
    if official_fact in positive_official and neg > 0:
        base = max(base, neg / total)
    if official_fact in negative_official and pos > 0:
        base = max(base, pos / total)
    return round(min(1.0, base), 3)


def staleness_score(last_verified_at: date | None, ttl_days: int, effective_today: date) -> float:
    if last_verified_at is None:
        return 1.0

    days_since_verification = (effective_today - last_verified_at).days
    lag_adjusted_days = max(0, days_since_verification - settings.pending_review_lag_days)
    return round(min(1.0, lag_adjusted_days / max(ttl_days, 1)), 3)


def _group_rows_by_property_facet(
    rows: list[ReviewEvidence],
) -> dict[tuple[str, str, str], list[ReviewEvidence]]:
    bucket: dict[tuple[str, str, str], list[ReviewEvidence]] = defaultdict(list)
    for row in rows:
        bucket[(row.property_id, row.amenity_id, row.facet)].append(row)
    return bucket


def _grouped_unique_counts(rows: list[ReviewEvidence]) -> dict[tuple[str, str], int]:
    bucket: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in rows:
        bucket[(row.amenity_id, row.facet)].add(row.review_id)
    return {key: len(review_ids) for key, review_ids in bucket.items()}


def rebuild_snapshots(db: Session, as_of: date | None = None) -> None:
    effective_today = lag_aware_today(as_of=as_of)
    recent_start = effective_today - timedelta(days=settings.recent_window_days)

    official_rows = db.execute(select(OfficialFact)).scalars().all()
    official_map: dict[str, dict[tuple[str, str], str]] = defaultdict(dict)
    for row in official_rows:
        official_map[row.property_id][(row.amenity_id, row.facet)] = row.official_fact

    property_ids = [property_id for (property_id,) in db.execute(select(Property.property_id)).all()]

    recent_review_counts = dict(
        db.execute(
            select(Review.property_id, func.count(Review.review_id))
            .where(Review.acquisition_date >= recent_start, Review.acquisition_date <= effective_today)
            .group_by(Review.property_id)
        ).all()
    )

    recent_evidence_rows = db.execute(
        select(ReviewEvidence).where(
            ReviewEvidence.acquisition_date >= recent_start,
            ReviewEvidence.acquisition_date <= effective_today,
        )
    ).scalars().all()
    all_evidence_rows = db.execute(select(ReviewEvidence)).scalars().all()

    recent_index = _group_rows_by_property_facet(recent_evidence_rows)
    all_index = _group_rows_by_property_facet(all_evidence_rows)

    global_recent_counts = _grouped_unique_counts(recent_evidence_rows)
    global_recent_review_count = max(1, sum(recent_review_counts.values()))
    learned_rates = {
        key: count / global_recent_review_count
        for key, count in global_recent_counts.items()
    }

    db.execute(delete(AmenitySnapshot))

    for property_id in property_ids:
        property_recent_review_count = recent_review_counts.get(property_id, 0)
        property_official = official_map[property_id]

        for amenity_id, facets in AMENITY_FACETS.items():
            amenity_listed = any(
                amenity == amenity_id and official_fact != "not_listed"
                for (amenity, _facet), official_fact in property_official.items()
            )

            for facet in facets:
                cfg = FACET_CONFIG[(amenity_id, facet)]
                official_fact = property_official.get((amenity_id, facet), "not_listed")

                current = recent_index.get((property_id, amenity_id, facet), [])
                historical = all_index.get((property_id, amenity_id, facet), [])

                actual_recent_coverage = len({row.review_id for row in current})
                lifetime_coverage = len({row.review_id for row in historical})
                recent_pos = sum(1 for row in current if row.polarity == "pos")
                recent_neg = sum(1 for row in current if row.polarity == "neg")
                recent_mixed = sum(1 for row in current if row.polarity == "mixed")
                last_verified_at = max(
                    (row.acquisition_date for row in historical if row.acquisition_date is not None),
                    default=None,
                )

                configured_rate = normalize_expected_rate(cfg.expected_rate)
                learned_rate = learned_rates.get((amenity_id, facet), 0.0)
                expected_rate = max(configured_rate, learned_rate)
                expected_recent_coverage = math.ceil(property_recent_review_count * expected_rate)

                if official_fact != "not_listed" or amenity_listed:
                    expected_recent_coverage = max(expected_recent_coverage, 1)

                coverage_gap = max(0, expected_recent_coverage - actual_recent_coverage) / max(expected_recent_coverage, 1)
                stale = staleness_score(last_verified_at, cfg.ttl_days, effective_today)
                conflict = contradiction_score(official_fact, recent_pos, recent_neg)

                if conflict >= 0.45 and (recent_pos + recent_neg) >= 2:
                    state = "CONFLICT"
                elif lifetime_coverage > 0 and actual_recent_coverage < expected_recent_coverage and stale >= 0.6:
                    state = "STALE"
                elif actual_recent_coverage < expected_recent_coverage:
                    state = "MISSING"
                else:
                    state = "SATURATED"

                explanation = (
                    f"official={official_fact}; actual_recent={actual_recent_coverage}; "
                    f"expected_recent={expected_recent_coverage}; last_verified_at={last_verified_at}; "
                    f"recent_pos={recent_pos}; recent_neg={recent_neg}; state={state}"
                )

                db.add(
                    AmenitySnapshot(
                        property_id=property_id,
                        amenity_id=amenity_id,
                        facet=facet,
                        official_fact=official_fact,
                        actual_recent_coverage=actual_recent_coverage,
                        lifetime_coverage=lifetime_coverage,
                        expected_recent_coverage=expected_recent_coverage,
                        recent_pos=recent_pos,
                        recent_neg=recent_neg,
                        recent_mixed=recent_mixed,
                        conflict_score=conflict,
                        coverage_gap=round(coverage_gap, 3),
                        staleness_score=stale,
                        state=state,
                        last_verified_at=last_verified_at,
                        snapshot_date=effective_today,
                        explanation=explanation,
                    )
                )

    db.commit()
