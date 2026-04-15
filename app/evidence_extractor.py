
import re

def _has_any(text: str, patterns: list[str]) -> bool:
    t = text.lower()
    return any(p in t for p in patterns)

def extract_review_evidences(text: str) -> list[dict]:
    t = text.lower()
    out: list[dict] = []

    # PARKING
    if "parking" in t:
        if _has_any(t, ["free parking", "parking was free", "complimentary parking"]):
            out.append({"amenity_id": "PARKING", "facet": "included", "polarity": "pos", "value": "included"})
        if _has_any(t, ["paid parking", "parking fee", "had to pay for parking", "parking cost"]):
            out.append({"amenity_id": "PARKING", "facet": "included", "polarity": "neg", "value": "surcharge"})
        if _has_any(t, ["hard to find the parking entrance", "parking entrance was hard to find"]):
            out.append({"amenity_id": "PARKING", "facet": "entrance_findability", "polarity": "neg", "value": "hard"})
        if _has_any(t, ["parking entrance easy to find", "easy to find parking entrance"]):
            out.append({"amenity_id": "PARKING", "facet": "entrance_findability", "polarity": "pos", "value": "easy"})

    # ROOM CLEANLINESS
    if _has_any(t, ["clean room", "room was clean", "spotless room"]):
        out.append({"amenity_id": "ROOM_CLEANLINESS", "facet": "surfaces_clean", "polarity": "pos", "value": "yes"})
    if _has_any(t, ["dirty room", "room was dirty", "dusty", "sticky floor", "stained furniture"]):
        out.append({"amenity_id": "ROOM_CLEANLINESS", "facet": "surfaces_clean", "polarity": "neg", "value": "no"})

    if _has_any(t, ["clean bedding", "fresh bedding", "fresh sheets"]):
        out.append({"amenity_id": "ROOM_CLEANLINESS", "facet": "bedding_clean", "polarity": "pos", "value": "yes"})
    if _has_any(t, ["dirty sheets", "stained sheets", "bedding smelled bad"]):
        out.append({"amenity_id": "ROOM_CLEANLINESS", "facet": "bedding_clean", "polarity": "neg", "value": "no"})

    if _has_any(t, ["smoke smell", "smelled like smoke"]):
        out.append({"amenity_id": "ROOM_CLEANLINESS", "facet": "odor", "polarity": "neg", "value": "smoke"})
    if _has_any(t, ["mold smell", "musty smell", "mildew smell"]):
        out.append({"amenity_id": "ROOM_CLEANLINESS", "facet": "odor", "polarity": "neg", "value": "mold"})

    # ROOM EXPERIENCE
    if _has_any(t, ["hair dryer", "hairdryer"]):
        out.append({"amenity_id": "ROOM_EXPERIENCE", "facet": "hair_dryer", "polarity": "pos", "value": "yes"})
    if _has_any(t, ["no hair dryer", "hair dryer missing"]):
        out.append({"amenity_id": "ROOM_EXPERIENCE", "facet": "hair_dryer", "polarity": "neg", "value": "no"})

    if _has_any(t, ["body wash provided", "had body wash"]):
        out.append({"amenity_id": "ROOM_EXPERIENCE", "facet": "body_wash", "polarity": "pos", "value": "yes"})
    if _has_any(t, ["no body wash", "body wash missing"]):
        out.append({"amenity_id": "ROOM_EXPERIENCE", "facet": "body_wash", "polarity": "neg", "value": "no"})

    if _has_any(t, ["complimentary water", "free water bottles", "bottled water provided"]):
        out.append({"amenity_id": "ROOM_EXPERIENCE", "facet": "water_bottles", "polarity": "pos", "value": "yes"})

    if _has_any(t, ["toiletries provided", "comb provided"]):
        out.append({"amenity_id": "ROOM_EXPERIENCE", "facet": "toiletries", "polarity": "pos", "value": "yes"})

    # BED / SLEEP
    m = re.search(r"(\d+)\s+pillows?", t)
    if m:
        n = int(m.group(1))
        out.append({
            "amenity_id": "BED_SLEEP",
            "facet": "pillow_count",
            "polarity": "pos",
            "value": "3_plus" if n >= 3 else str(n),
        })

    if _has_any(t, ["blackout curtains", "curtains blocked light"]):
        out.append({"amenity_id": "BED_SLEEP", "facet": "light_blocking", "polarity": "pos", "value": "good"})
    if _has_any(t, ["light came through the curtains", "curtains did not block light"]):
        out.append({"amenity_id": "BED_SLEEP", "facet": "light_blocking", "polarity": "neg", "value": "poor"})

    # NOISE
    if _has_any(t, ["hallway noise", "noise from hallway", "street noise", "neighbors were noisy", "outside noise"]):
        out.append({"amenity_id": "NOISE", "facet": "external_noise", "polarity": "neg", "value": "too_noisy"})
    if _has_any(t, ["quiet room", "very quiet at night"]):
        out.append({"amenity_id": "NOISE", "facet": "external_noise", "polarity": "pos", "value": "quiet"})

    if _has_any(t, ["loud air conditioning", "noisy ac", "heater was noisy"]):
        out.append({"amenity_id": "NOISE", "facet": "hvac_noise", "polarity": "neg", "value": "too_noisy"})

    # ROOM INFRA
    if _has_any(t, ["dim lighting", "too dark"]):
        out.append({"amenity_id": "ROOM_INFRA", "facet": "lighting", "polarity": "neg", "value": "poor"})
    if _has_any(t, ["good lighting", "bright room"]):
        out.append({"amenity_id": "ROOM_INFRA", "facet": "lighting", "polarity": "pos", "value": "good"})

    if _has_any(t, ["ac worked", "heater worked", "temperature control worked"]):
        out.append({"amenity_id": "ROOM_INFRA", "facet": "hvac_working", "polarity": "pos", "value": "working"})
    if _has_any(t, ["ac broken", "heater broken", "air conditioning did not work", "heating did not work"]):
        out.append({"amenity_id": "ROOM_INFRA", "facet": "hvac_working", "polarity": "neg", "value": "not_working"})

    if "wifi" in t or "wi-fi" in t:
        if _has_any(t, ["free wifi", "free wi-fi", "wifi included", "wi-fi included"]):
            out.append({"amenity_id": "ROOM_INFRA", "facet": "wifi_fee", "polarity": "pos", "value": "included"})
        if _has_any(t, ["paid wifi", "wifi fee", "had to pay for wifi", "premium internet"]):
            out.append({"amenity_id": "ROOM_INFRA", "facet": "wifi_fee", "polarity": "neg", "value": "surcharge"})
        if _has_any(t, ["no wifi", "wifi unavailable", "wi-fi unavailable"]):
            out.append({"amenity_id": "ROOM_INFRA", "facet": "wifi_available", "polarity": "neg", "value": "no"})
        else:
            out.append({"amenity_id": "ROOM_INFRA", "facet": "wifi_available", "polarity": "pos", "value": "yes"})

    # ROOM SERVICE
    if "breakfast" in t:
        if _has_any(t, ["breakfast included", "free breakfast", "complimentary breakfast"]):
            out.append({"amenity_id": "ROOM_SERVICE", "facet": "breakfast_included", "polarity": "pos", "value": "included"})
        elif _has_any(t, ["breakfast cost", "paid breakfast", "breakfast not included"]):
            out.append({"amenity_id": "ROOM_SERVICE", "facet": "breakfast_included", "polarity": "neg", "value": "surcharge"})
        elif _has_any(t, ["no breakfast", "breakfast unavailable"]):
            out.append({"amenity_id": "ROOM_SERVICE", "facet": "breakfast_included", "polarity": "neg", "value": "not_available"})

    if _has_any(t, ["vegetarian options", "kids options", "dietary options", "gluten free"]):
        out.append({"amenity_id": "ROOM_SERVICE", "facet": "dietary_options", "polarity": "pos", "value": "yes"})

    if _has_any(t, ["room service", "late night food", "food available late"]):
        out.append({"amenity_id": "ROOM_SERVICE", "facet": "late_food", "polarity": "pos", "value": "yes"})

    # HOTEL INFRA
    if _has_any(t, ["elevator", "lift"]):
        out.append({"amenity_id": "HOTEL_INFRA", "facet": "elevator", "polarity": "pos", "value": "yes"})
    if _has_any(t, ["no elevator"]):
        out.append({"amenity_id": "HOTEL_INFRA", "facet": "elevator", "polarity": "neg", "value": "no"})

    if _has_any(t, ["luggage storage", "stored our luggage"]):
        out.append({"amenity_id": "HOTEL_INFRA", "facet": "luggage_storage", "polarity": "pos", "value": "yes"})

    if "shuttle" in t:
        if _has_any(t, ["free shuttle"]):
            out.append({"amenity_id": "HOTEL_INFRA", "facet": "shuttle", "polarity": "pos", "value": "available_included"})
        elif _has_any(t, ["paid shuttle", "shuttle fee"]):
            out.append({"amenity_id": "HOTEL_INFRA", "facet": "shuttle", "polarity": "neg", "value": "available_surcharge"})
        elif _has_any(t, ["no shuttle", "shuttle unavailable"]):
            out.append({"amenity_id": "HOTEL_INFRA", "facet": "shuttle", "polarity": "neg", "value": "not_available"})

    if _has_any(t, ["bus stop nearby", "public transportation nearby", "metro nearby", "subway nearby"]):
        out.append({"amenity_id": "HOTEL_INFRA", "facet": "public_transport", "polarity": "pos", "value": "yes"})

    if _has_any(t, ["good restaurants nearby", "lots of restaurants nearby"]):
        out.append({"amenity_id": "HOTEL_INFRA", "facet": "nearby_restaurants", "polarity": "pos", "value": "good"})
    if _has_any(t, ["few restaurants nearby", "bad restaurants nearby", "limited dining nearby"]):
        out.append({"amenity_id": "HOTEL_INFRA", "facet": "nearby_restaurants", "polarity": "neg", "value": "limited"})

    return out