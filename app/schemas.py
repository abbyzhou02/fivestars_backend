from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SnapshotRowResponse(BaseModel):
    amenity_id: str
    facet: str
    official_fact: str
    actual_recent_coverage: int
    lifetime_coverage: int
    expected_recent_coverage: int
    recent_pos: int
    recent_neg: int
    recent_mixed: int
    conflict_score: float
    coverage_gap: float
    staleness_score: float
    state: str
    last_verified_at: date | None = None
    explanation: str | None = None

    model_config = ConfigDict(from_attributes=True)


class FollowupRequest(BaseModel):
    draft_text: str | None = None
    asked_facets: list[Any] = Field(default_factory=list)
    stay_date: date | None = None


class FollowupResponse(BaseModel):
    property_id: str
    amenity_id: str
    facet: str
    state: str
    score: float
    question_text: str
    options: list[dict[str, str]]
    debug: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class CandidateResponse(FollowupResponse):
    pass


class AnswerCreateRequest(BaseModel):
    property_id: str
    review_session_id: str | None = None
    amenity_id: str
    facet: str
    question_text: str
    answer_value: str | None = None
    answer_text: str | None = None


class AnswerCreateResponse(BaseModel):
    status: str
    stored_at: datetime
