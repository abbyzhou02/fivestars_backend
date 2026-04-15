from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import typer
from sqlalchemy import delete

from app.db import Base, SessionLocal, engine
from app.evidence_extractor import EXTRACTOR_VERSION, extract_review_evidence
from app.models import OfficialFact, Property, Review, ReviewEvidence
from app.official_facts import extract_official_facts
from app.snapshot_builder import rebuild_snapshots
from app.utils import make_review_id, normalize_whitespace, parse_date_safe, parse_rating_overall

app = typer.Typer(add_completion=False)


@app.command()
def main(
    description_csv: str = typer.Option(..., help="Path to Description_PROC csv"),
    reviews_csv: str = typer.Option(..., help="Path to Reviews_PROC csv"),
) -> None:
    desc_path = Path(description_csv)
    reviews_path = Path(reviews_csv)

    if not desc_path.exists():
        raise typer.BadParameter(f"Description CSV not found: {desc_path}")
    if not reviews_path.exists():
        raise typer.BadParameter(f"Reviews CSV not found: {reviews_path}")

    desc_df = pd.read_csv(desc_path)
    reviews_df = pd.read_csv(reviews_path)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        db.execute(delete(ReviewEvidence))
        db.execute(delete(OfficialFact))
        db.execute(delete(Review))
        db.execute(delete(Property))
        db.commit()

        for _, row in desc_df.iterrows():
            payload = {col: (None if pd.isna(row[col]) else row[col]) for col in desc_df.columns}

            db.add(
                Property(
                    property_id=str(payload["eg_property_id"]),
                    city=payload.get("city"),
                    province=payload.get("province"),
                    country=payload.get("country"),
                    star_rating=float(payload["star_rating"]) if payload.get("star_rating") is not None else None,
                    guest_rating_avg=float(payload["guestrating_avg_expedia"]) if payload.get("guestrating_avg_expedia") is not None else None,
                    popular_amenities_list=payload.get("popular_amenities_list"),
                    description_blob=json.dumps(payload, ensure_ascii=False, default=str),
                )
            )
        db.commit()

        for _, row in desc_df.iterrows():
            payload = {col: (None if pd.isna(row[col]) else row[col]) for col in desc_df.columns}
            property_id = str(payload["eg_property_id"])
            for fact in extract_official_facts(payload):
                db.add(
                    OfficialFact(
                        property_id=property_id,
                        amenity_id=fact.amenity_id,
                        facet=fact.facet,
                        official_fact=fact.official_fact,
                        source_field=fact.source_field,
                        source_text=fact.source_text,
                    )
                )
        db.commit()

        for _, row in reviews_df.iterrows():
            property_id = str(row["eg_property_id"])
            acquisition_date = parse_date_safe(row.get("acquisition_date"))
            review_title = None if pd.isna(row.get("review_title")) else str(row.get("review_title"))
            review_text = None if pd.isna(row.get("review_text")) else str(row.get("review_text"))
            full_text = normalize_whitespace(f"{review_title or ''}. {review_text or ''}")
            review_id = make_review_id(property_id, acquisition_date, review_title, review_text)

            db.add(
                Review(
                    review_id=review_id,
                    property_id=property_id,
                    acquisition_date=acquisition_date,
                    lob=None if pd.isna(row.get("lob")) else str(row.get("lob")),
                    overall_rating=parse_rating_overall(row.get("rating")),
                    rating_raw=None if pd.isna(row.get("rating")) else str(row.get("rating")),
                    review_title=review_title,
                    review_text=review_text,
                    full_text=full_text,
                )
            )
        db.commit()

        reviews = db.query(Review).all()
        for review in reviews:
            if not review.full_text:
                continue
            for evidence in extract_review_evidence(review.full_text):
                db.add(
                    ReviewEvidence(
                        review_id=review.review_id,
                        property_id=review.property_id,
                        acquisition_date=review.acquisition_date,
                        amenity_id=evidence.amenity_id,
                        facet=evidence.facet,
                        polarity=evidence.polarity,
                        confidence=evidence.confidence,
                        evidence_text=evidence.evidence_text,
                        extractor_version=EXTRACTOR_VERSION,
                    )
                )
        db.commit()

        rebuild_snapshots(db=db)
        typer.echo("Bootstrap complete.")
    finally:
        db.close()


if __name__ == "__main__":
    app()
