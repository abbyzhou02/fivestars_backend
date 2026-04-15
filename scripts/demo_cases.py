from __future__ import annotations

from sqlalchemy import select

from app.db import SessionLocal
from app.followup import top_candidates
from app.models import Property


TARGET_CITIES = ["Broomfield", "Monterey", "Ocala", "Frisco"]


def main() -> None:
    db = SessionLocal()
    try:
        properties = db.execute(select(Property)).scalars().all()
        by_city = {row.city: row for row in properties}

        for city in TARGET_CITIES:
            row = by_city.get(city)
            if row is None:
                continue

            print(f"\n=== {city} ===")
            candidates = top_candidates(db=db, property_id=row.property_id, draft_text="", asked_facets=[], limit=5)
            for idx, c in enumerate(candidates, start=1):
                print(
                    f"{idx}. {c.amenity_id} × {c.facet} | state={c.state} | score={c.score} | {c.question_text}"
                )
                print(f"   debug={c.debug}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
