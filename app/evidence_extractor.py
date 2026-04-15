from __future__ import annotations

import re
from dataclasses import dataclass


EXTRACTOR_VERSION = "rules_v2"


@dataclass(frozen=True)
class ReviewEvidenceRecord:
    amenity_id: str
    facet: str
    polarity: str
    confidence: float
    evidence_text: str
    value: str | None = None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def _find_any(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        if pattern in text:
            return pattern
    return None


def _append(
    out: list[ReviewEvidenceRecord],
    seen: set[tuple[str, str, str, str | None]],
    *,
    amenity_id: str,
    facet: str,
    polarity: str,
    evidence_text: str,
    value: str | None = None,
    confidence: float = 0.82,
) -> None:
    key = (amenity_id, facet, polarity, value)
    if key in seen:
        return
    seen.add(key)
    out.append(
        ReviewEvidenceRecord(
            amenity_id=amenity_id,
            facet=facet,
            polarity=polarity,
            confidence=confidence,
            evidence_text=evidence_text,
            value=value,
        )
    )


def extract_review_evidence(text: str) -> list[ReviewEvidenceRecord]:
    t = _normalize(text)
    out: list[ReviewEvidenceRecord] = []
    seen: set[tuple[str, str, str, str | None]] = set()

    # ---------------------------
    # PARKING
    # ---------------------------

    if "parking" in t:
        match = _find_any(t, ["paid parking", "parking fee", "had to pay for parking", "parking cost"])
        if match:
            _append(
                out,
                seen,
                amenity_id="PARKING",
                facet="included",
                polarity="neg",
                evidence_text=match,
                value="surcharge",
            )
        else:
            match = _find_any(t, ["free parking", "parking was free", "complimentary parking"])
            if match:
                _append(
                    out,
                    seen,
                    amenity_id="PARKING",
                    facet="included",
                    polarity="pos",
                    evidence_text=match,
                    value="included",
                )

        match = _find_any(t, ["hard to find the parking entrance", "parking entrance was hard to find"])
        if match:
            _append(
                out,
                seen,
                amenity_id="PARKING",
                facet="entrance_findability",
                polarity="neg",
                evidence_text=match,
                value="hard",
            )
        else:
            match = _find_any(t, ["parking entrance easy to find", "easy to find parking entrance"])
            if match:
                _append(
                    out,
                    seen,
                    amenity_id="PARKING",
                    facet="entrance_findability",
                    polarity="pos",
                    evidence_text=match,
                    value="easy",
                )

    # ---------------------------
    # ROOM CLEANLINESS
    # ---------------------------

    match = _find_any(t, ["dirty room", "room was dirty", "dusty", "sticky floor", "stained furniture"])
    if match:
        _append(
            out,
            seen,
            amenity_id="ROOM_CLEANLINESS",
            facet="surfaces_clean",
            polarity="neg",
            evidence_text=match,
            value="no",
        )
    else:
        match = _find_any(t, ["clean room", "room was clean", "spotless room"])
        if match:
            _append(
                out,
                seen,
                amenity_id="ROOM_CLEANLINESS",
                facet="surfaces_clean",
                polarity="pos",
                evidence_text=match,
                value="yes",
            )

    match = _find_any(t, ["dirty sheets", "stained sheets", "bedding smelled bad"])
    if match:
        _append(
            out,
            seen,
            amenity_id="ROOM_CLEANLINESS",
            facet="bedding_clean",
            polarity="neg",
            evidence_text=match,
            value="no",
        )
    else:
        match = _find_any(t, ["clean bedding", "fresh bedding", "fresh sheets"])
        if match:
            _append(
                out,
                seen,
                amenity_id="ROOM_CLEANLINESS",
                facet="bedding_clean",
                polarity="pos",
                evidence_text=match,
                value="yes",
            )

    match = _find_any(t, ["smoke smell", "smelled like smoke"])
    if match:
        _append(
            out,
            seen,
            amenity_id="ROOM_CLEANLINESS",
            facet="odor",
            polarity="neg",
            evidence_text=match,
            value="smoke",
        )
    else:
        match = _find_any(t, ["mold smell", "musty smell", "mildew smell"])
        if match:
            _append(
                out,
                seen,
                amenity_id="ROOM_CLEANLINESS",
                facet="odor",
                polarity="neg",
                evidence_text=match,
                value="mold",
            )
        else:
            match = _find_any(t, ["no smell", "no odor", "fresh smelling room", "room smelled fresh"])
            if match:
                _append(
                    out,
                    seen,
                    amenity_id="ROOM_CLEANLINESS",
                    facet="odor",
                    polarity="pos",
                    evidence_text=match,
                    value="no_odor",
                )

    # ---------------------------
    # ROOM EXPERIENCE
    # ---------------------------

    match = _find_any(t, ["no hair dryer", "hair dryer missing", "hairdryer missing"])
    if match:
        _append(
            out,
            seen,
            amenity_id="ROOM_EXPERIENCE",
            facet="hair_dryer",
            polarity="neg",
            evidence_text=match,
            value="no",
        )
    else:
        match = _find_any(t, ["hair dryer", "hairdryer"])
        if match:
            _append(
                out,
                seen,
                amenity_id="ROOM_EXPERIENCE",
                facet="hair_dryer",
                polarity="pos",
                evidence_text=match,
                value="yes",
                confidence=0.74,
            )

    match = _find_any(t, ["no body wash", "body wash missing"])
    if match:
        _append(
            out,
            seen,
            amenity_id="ROOM_EXPERIENCE",
            facet="body_wash",
            polarity="neg",
            evidence_text=match,
            value="no",
        )
    else:
        match = _find_any(t, ["body wash provided", "had body wash"])
        if match:
            _append(
                out,
                seen,
                amenity_id="ROOM_EXPERIENCE",
                facet="body_wash",
                polarity="pos",
                evidence_text=match,
                value="yes",
            )

    match = _find_any(t, ["complimentary water", "free water bottles", "bottled water provided"])
    if match:
        _append(
            out,
            seen,
            amenity_id="ROOM_EXPERIENCE",
            facet="water_bottles",
            polarity="pos",
            evidence_text=match,
            value="yes",
        )

    match = _find_any(t, ["toiletries provided", "comb provided"])
    if match:
        _append(
            out,
            seen,
            amenity_id="ROOM_EXPERIENCE",
            facet="toiletries",
            polarity="pos",
            evidence_text=match,
            value="yes",
        )

    # ---------------------------
    # BED / SLEEP
    # ---------------------------

    pillow_match = re.search(r"\b(\d+)\s+pillows?\b", t)
    if pillow_match:
        count = int(pillow_match.group(1))
        _append(
            out,
            seen,
            amenity_id="BED_SLEEP",
            facet="pillow_count",
            polarity="pos",
            evidence_text=pillow_match.group(0),
            value="3_plus" if count >= 3 else str(count),
        )

    match = _find_any(t, ["light came through the curtains", "curtains did not block light"])
    if match:
        _append(
            out,
            seen,
            amenity_id="BED_SLEEP",
            facet="light_blocking",
            polarity="neg",
            evidence_text=match,
            value="poor",
        )
    else:
        match = _find_any(t, ["blackout curtains", "curtains blocked light"])
        if match:
            _append(
                out,
                seen,
                amenity_id="BED_SLEEP",
                facet="light_blocking",
                polarity="pos",
                evidence_text=match,
                value="good",
            )

    # ---------------------------
    # NOISE
    # ---------------------------

    match = _find_any(
        t,
        ["hallway noise", "noise from hallway", "street noise", "neighbors were noisy", "outside noise"],
    )
    if match:
        _append(
            out,
            seen,
            amenity_id="NOISE",
            facet="external_noise",
            polarity="neg",
            evidence_text=match,
            value="too_noisy",
        )
    else:
        match = _find_any(t, ["quiet room", "very quiet at night"])
        if match:
            _append(
                out,
                seen,
                amenity_id="NOISE",
                facet="external_noise",
                polarity="pos",
                evidence_text=match,
                value="quiet",
            )

    match = _find_any(t, ["loud air conditioning", "noisy ac", "heater was noisy"])
    if match:
        _append(
            out,
            seen,
            amenity_id="NOISE",
            facet="hvac_noise",
            polarity="neg",
            evidence_text=match,
            value="too_noisy",
        )
    else:
        match = _find_any(t, ["quiet ac", "air conditioning was quiet", "heater was quiet"])
        if match:
            _append(
                out,
                seen,
                amenity_id="NOISE",
                facet="hvac_noise",
                polarity="pos",
                evidence_text=match,
                value="quiet",
            )

    # ---------------------------
    # ROOM INFRA
    # ---------------------------

    match = _find_any(t, ["dim lighting", "too dark"])
    if match:
        _append(
            out,
            seen,
            amenity_id="ROOM_INFRA",
            facet="lighting",
            polarity="neg",
            evidence_text=match,
            value="poor",
        )
    else:
        match = _find_any(t, ["good lighting", "bright room"])
        if match:
            _append(
                out,
                seen,
                amenity_id="ROOM_INFRA",
                facet="lighting",
                polarity="pos",
                evidence_text=match,
                value="good",
            )

    match = _find_any(t, ["ac broken", "heater broken", "air conditioning did not work", "heating did not work"])
    if match:
        _append(
            out,
            seen,
            amenity_id="ROOM_INFRA",
            facet="hvac_working",
            polarity="neg",
            evidence_text=match,
            value="not_working",
        )
    else:
        match = _find_any(t, ["ac worked", "heater worked", "temperature control worked"])
        if match:
            _append(
                out,
                seen,
                amenity_id="ROOM_INFRA",
                facet="hvac_working",
                polarity="pos",
                evidence_text=match,
                value="working",
            )

    if "wifi" in t or "wi-fi" in t:
        match = _find_any(t, ["no wifi", "wifi unavailable", "wi-fi unavailable"])
        if match:
            _append(
                out,
                seen,
                amenity_id="ROOM_INFRA",
                facet="wifi_available",
                polarity="neg",
                evidence_text=match,
                value="no",
            )
        else:
            _append(
                out,
                seen,
                amenity_id="ROOM_INFRA",
                facet="wifi_available",
                polarity="pos",
                evidence_text="wifi mentioned",
                value="yes",
                confidence=0.70,
            )

        match = _find_any(t, ["paid wifi", "wifi fee", "had to pay for wifi", "premium internet"])
        if match:
            _append(
                out,
                seen,
                amenity_id="ROOM_INFRA",
                facet="wifi_fee",
                polarity="neg",
                evidence_text=match,
                value="surcharge",
            )
        else:
            match = _find_any(t, ["free wifi", "free wi-fi", "wifi included", "wi-fi included"])
            if match:
                _append(
                    out,
                    seen,
                    amenity_id="ROOM_INFRA",
                    facet="wifi_fee",
                    polarity="pos",
                    evidence_text=match,
                    value="included",
                )

    # ---------------------------
    # BREAKFAST / ROOM SERVICE
    # ---------------------------

    if "breakfast" in t:
        match = _find_any(t, ["paid breakfast", "breakfast cost", "breakfast not included"])
        if match:
            _append(
                out,
                seen,
                amenity_id="ROOM_SERVICE",
                facet="breakfast_included",
                polarity="neg",
                evidence_text=match,
                value="surcharge",
            )
        else:
            match = _find_any(t, ["no breakfast", "breakfast unavailable"])
            if match:
                _append(
                    out,
                    seen,
                    amenity_id="ROOM_SERVICE",
                    facet="breakfast_included",
                    polarity="neg",
                    evidence_text=match,
                    value="not_available",
                )
            else:
                match = _find_any(t, ["breakfast included", "free breakfast", "complimentary breakfast"])
                if match:
                    _append(
                        out,
                        seen,
                        amenity_id="ROOM_SERVICE",
                        facet="breakfast_included",
                        polarity="pos",
                        evidence_text=match,
                        value="included",
                    )

    match = _find_any(t, ["vegetarian options", "kids options", "dietary options", "gluten free"])
    if match:
        _append(
            out,
            seen,
            amenity_id="ROOM_SERVICE",
            facet="dietary_options",
            polarity="pos",
            evidence_text=match,
            value="yes",
        )

    match = _find_any(t, ["room service", "late night food", "food available late"])
    if match:
        _append(
            out,
            seen,
            amenity_id="ROOM_SERVICE",
            facet="late_food",
            polarity="pos",
            evidence_text=match,
            value="yes",
        )

    # ---------------------------
    # HOTEL INFRA
    # ---------------------------

    match = _find_any(t, ["no elevator"])
    if match:
        _append(
            out,
            seen,
            amenity_id="HOTEL_INFRA",
            facet="elevator",
            polarity="neg",
            evidence_text=match,
            value="no",
        )
    else:
        match = _find_any(t, ["elevator", "lift"])
        if match:
            _append(
                out,
                seen,
                amenity_id="HOTEL_INFRA",
                facet="elevator",
                polarity="pos",
                evidence_text=match,
                value="yes",
                confidence=0.72,
            )

    match = _find_any(t, ["luggage storage", "stored our luggage"])
    if match:
        _append(
            out,
            seen,
            amenity_id="HOTEL_INFRA",
            facet="luggage_storage",
            polarity="pos",
            evidence_text=match,
            value="yes",
        )

    if "shuttle" in t:
        match = _find_any(t, ["no shuttle", "shuttle unavailable"])
        if match:
            _append(
                out,
                seen,
                amenity_id="HOTEL_INFRA",
                facet="shuttle",
                polarity="neg",
                evidence_text=match,
                value="not_available",
            )
        else:
            match = _find_any(t, ["paid shuttle", "shuttle fee"])
            if match:
                _append(
                    out,
                    seen,
                    amenity_id="HOTEL_INFRA",
                    facet="shuttle",
                    polarity="neg",
                    evidence_text=match,
                    value="available_surcharge",
                )
            else:
                match = _find_any(t, ["free shuttle"])
                if match:
                    _append(
                        out,
                        seen,
                        amenity_id="HOTEL_INFRA",
                        facet="shuttle",
                        polarity="pos",
                        evidence_text=match,
                        value="available_included",
                    )

    match = _find_any(t, ["bus stop nearby", "public transportation nearby", "metro nearby", "subway nearby"])
    if match:
        _append(
            out,
            seen,
            amenity_id="HOTEL_INFRA",
            facet="public_transport",
            polarity="pos",
            evidence_text=match,
            value="yes",
        )

    match = _find_any(t, ["few restaurants nearby", "limited dining nearby"])
    if match:
        _append(
            out,
            seen,
            amenity_id="HOTEL_INFRA",
            facet="nearby_restaurants",
            polarity="neg",
            evidence_text=match,
            value="limited",
        )
    else:
        match = _find_any(t, ["good restaurants nearby", "lots of restaurants nearby"])
        if match:
            _append(
                out,
                seen,
                amenity_id="HOTEL_INFRA",
                facet="nearby_restaurants",
                polarity="pos",
                evidence_text=match,
                value="good",
            )

    return out
