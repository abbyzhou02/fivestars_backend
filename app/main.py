from __future__ import annotations

from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .followup import pick_followup, top_candidates
from .models import AmenitySnapshot, FollowupAnswer, Property
from .schemas import (
    AnswerCreateRequest,
    AnswerCreateResponse,
    CandidateResponse,
    FollowupRequest,
    FollowupResponse,
    SnapshotRowResponse,
)
from .settings import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/v1/properties")
def list_properties(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(Property)).scalars().all()
    return [
        {
            "property_id": row.property_id,
            "city": row.city,
            "province": row.province,
            "country": row.country,
        }
        for row in rows
    ]


@app.get("/v1/properties/{property_id}/snapshot", response_model=list[SnapshotRowResponse])
def get_snapshot(property_id: str, db: Session = Depends(get_db)) -> list[SnapshotRowResponse]:
    rows = db.execute(
        select(AmenitySnapshot)
        .where(AmenitySnapshot.property_id == property_id)
        .order_by(AmenitySnapshot.amenity_id, AmenitySnapshot.facet)
    ).scalars().all()

    if not rows:
        raise HTTPException(status_code=404, detail="No snapshot found for this property_id.")

    return [
        SnapshotRowResponse(
            amenity_id=row.amenity_id,
            facet=row.facet,
            official_fact=row.official_fact,
            actual_recent_coverage=row.actual_recent_coverage,
            lifetime_coverage=row.lifetime_coverage,
            expected_recent_coverage=row.expected_recent_coverage,
            recent_pos=row.recent_pos,
            recent_neg=row.recent_neg,
            recent_mixed=row.recent_mixed,
            conflict_score=row.conflict_score,
            coverage_gap=row.coverage_gap,
            staleness_score=row.staleness_score,
            state=row.state,
            last_verified_at=row.last_verified_at,
            explanation=row.explanation,
        )
        for row in rows
    ]


@app.post("/v1/properties/{property_id}/followup", response_model=FollowupResponse | None)
def choose_followup(
    property_id: str,
    payload: FollowupRequest,
    db: Session = Depends(get_db),
) -> FollowupResponse | None:
    candidate = pick_followup(
        db=db,
        property_id=property_id,
        draft_text=payload.draft_text,
        asked_facets=payload.asked_facets,
        stay_date=payload.stay_date,
    )
    if candidate is None:
        return None

    return FollowupResponse(
        property_id=candidate.property_id,
        amenity_id=candidate.amenity_id,
        facet=candidate.facet,
        state=candidate.state,
        score=candidate.score,
        question_text=candidate.question_text,
        options=candidate.options,
        debug=candidate.debug,
    )


@app.post("/v1/properties/{property_id}/candidates", response_model=list[CandidateResponse])
def rank_candidates(
    property_id: str,
    payload: FollowupRequest,
    db: Session = Depends(get_db),
) -> list[CandidateResponse]:
    candidates = top_candidates(
        db=db,
        property_id=property_id,
        draft_text=payload.draft_text,
        asked_facets=payload.asked_facets,
        limit=5,
    )
    return [
        CandidateResponse(
            property_id=c.property_id,
            amenity_id=c.amenity_id,
            facet=c.facet,
            state=c.state,
            score=c.score,
            question_text=c.question_text,
            options=c.options,
            debug=c.debug,
        )
        for c in candidates
    ]


@app.post("/v1/followup-answers", response_model=AnswerCreateResponse)
def store_answer(payload: AnswerCreateRequest, db: Session = Depends(get_db)) -> AnswerCreateResponse:
    now = datetime.utcnow()
    db.add(
        FollowupAnswer(
            property_id=payload.property_id,
            review_session_id=payload.review_session_id,
            amenity_id=payload.amenity_id,
            facet=payload.facet,
            question_text=payload.question_text,
            answer_value=payload.answer_value,
            answer_text=payload.answer_text,
            answered_at=now,
        )
    )
    db.commit()
    return AnswerCreateResponse(status="ok", stored_at=now)
