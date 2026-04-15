from __future__ import annotations

from datetime import date, datetime
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


class Property(Base):
    __tablename__ = "properties"

    property_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    province: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    star_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    guest_rating_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    popular_amenities_list: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_blob: Mapped[str | None] = mapped_column(Text, nullable=True)

    reviews: Mapped[list["Review"]] = relationship(back_populates="property")
    official_facts: Mapped[list["OfficialFact"]] = relationship(back_populates="property")
    snapshots: Mapped[list["AmenitySnapshot"]] = relationship(back_populates="property")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(String, index=True)    
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.property_id"), index=True)
    acquisition_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    lob: Mapped[str | None] = mapped_column(String(64), nullable=True)
    overall_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    property: Mapped["Property"] = relationship(back_populates="reviews")
    evidences: Mapped[list["ReviewEvidence"]] = relationship(back_populates="review")


class OfficialFact(Base):
    __tablename__ = "official_facts"
    __table_args__ = (
        UniqueConstraint("property_id", "amenity_id", "facet", name="uq_official_fact"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.property_id"), index=True)
    amenity_id: Mapped[str] = mapped_column(String(64), index=True)
    facet: Mapped[str] = mapped_column(String(64), index=True)
    official_fact: Mapped[str] = mapped_column(String(64), index=True)
    source_field: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    property: Mapped["Property"] = relationship(back_populates="official_facts")


class ReviewEvidence(Base):
    __tablename__ = "review_evidences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.review_id"), index=True)
    property_id: Mapped[str] = mapped_column(String(128), index=True)
    acquisition_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    amenity_id: Mapped[str] = mapped_column(String(64), index=True)
    facet: Mapped[str] = mapped_column(String(64), index=True)
    polarity: Mapped[str] = mapped_column(String(16), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    evidence_text: Mapped[str] = mapped_column(Text)
    extractor_version: Mapped[str] = mapped_column(String(32), default="rules_v1")

    review: Mapped["Review"] = relationship(back_populates="evidences")


class AmenitySnapshot(Base):
    __tablename__ = "amenity_snapshots"
    __table_args__ = (
        UniqueConstraint("property_id", "amenity_id", "facet", name="uq_snapshot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.property_id"), index=True)
    amenity_id: Mapped[str] = mapped_column(String(64), index=True)
    facet: Mapped[str] = mapped_column(String(64), index=True)
    official_fact: Mapped[str] = mapped_column(String(64), default="not_listed")
    actual_recent_coverage: Mapped[int] = mapped_column(Integer, default=0)
    lifetime_coverage: Mapped[int] = mapped_column(Integer, default=0)
    expected_recent_coverage: Mapped[int] = mapped_column(Integer, default=0)
    recent_pos: Mapped[int] = mapped_column(Integer, default=0)
    recent_neg: Mapped[int] = mapped_column(Integer, default=0)
    recent_mixed: Mapped[int] = mapped_column(Integer, default=0)
    conflict_score: Mapped[float] = mapped_column(Float, default=0.0)
    coverage_gap: Mapped[float] = mapped_column(Float, default=0.0)
    staleness_score: Mapped[float] = mapped_column(Float, default=0.0)
    state: Mapped[str] = mapped_column(String(32), default="MISSING")
    last_verified_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    property: Mapped["Property"] = relationship(back_populates="snapshots")


class FollowupAnswer(Base):
    __tablename__ = "followup_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(String(128), index=True)
    review_session_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    amenity_id: Mapped[str] = mapped_column(String(64), index=True)
    facet: Mapped[str] = mapped_column(String(64), index=True)
    question_text: Mapped[str] = mapped_column(Text)
    answer_value: Mapped[str | None] = mapped_column(String(64), nullable=True)
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    answered_at: Mapped[datetime] = mapped_column(DateTime)
