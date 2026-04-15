from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OfficialFactRecord:
    amenity_id: str
    facet: str
    official_fact: str
    source_field: str
    source_text: str | None = None


OFFICIAL_FACT_MAPPINGS = [
    ("property_amenity_parking", "PARKING", "included", "listed"),
    ("property_amenity_wifi", "ROOM_INFRA", "wifi_available", "listed"),
    ("property_amenity_breakfast", "ROOM_SERVICE", "breakfast_included", "listed"),
    ("property_amenity_elevator", "HOTEL_INFRA", "elevator", "listed"),
    ("property_amenity_shuttle", "HOTEL_INFRA", "shuttle", "listed"),
]


def _truthy(value: object) -> bool:
    if value is None:
        return False

    normalized = str(value).strip().lower()
    return normalized in {
        "1",
        "true",
        "yes",
        "y",
        "t",
        "available",
        "included",
        "listed",
    }


def _source_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def extract_official_facts(row: dict) -> list[OfficialFactRecord]:
    facts: list[OfficialFactRecord] = []

    for column, amenity_id, facet, truth_value in OFFICIAL_FACT_MAPPINGS:
        raw_value = row.get(column)
        facts.append(
            OfficialFactRecord(
                amenity_id=amenity_id,
                facet=facet,
                official_fact=truth_value if _truthy(raw_value) else "not_listed",
                source_field=column,
                source_text=_source_text(raw_value),
            )
        )

    return facts
