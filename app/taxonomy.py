
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class FacetConfig:
    question_text: str
    options: list[dict[str, str]]
    expected_rate: int
    ttl_days: int
    business_importance: float
    answerability: float = 0.9


TAXONOMY: dict[str, dict[str, FacetConfig]] = {
    "PARKING": {
        "included": FacetConfig(
            question_text="Was parking free, or did it cost extra?",
            options=[
                {"label": "Free", "value": "included"},
                {"label": "Cost extra", "value": "surcharge"},
                {"label": "No parking", "value": "not_available"},
                {"label": "Didn't use it", "value": "not_applicable"},
            ],
            expected_rate=2,
            ttl_days=180,
            business_importance=0.9,
        ),
        "entrance_findability": FacetConfig(
            question_text="Was the parking entrance easy to find?",
            options=[
                {"label": "Easy to find", "value": "easy"},
                {"label": "Hard to find", "value": "hard"},
                {"label": "Didn't use it", "value": "not_applicable"},
            ],
            expected_rate=1,
            ttl_days=240,
            business_importance=0.6,
        ),
    },

    "ROOM_CLEANLINESS": {
        "surfaces_clean": FacetConfig(
            question_text="Were the floors, surfaces, and furniture clean?",
            options=[
                {"label": "Clean", "value": "yes"},
                {"label": "Not clean", "value": "no"},
            ],
            expected_rate=2,
            ttl_days=90,
            business_importance=0.95,
        ),
        "bedding_clean": FacetConfig(
            question_text="Did the bedding feel fresh and clean?",
            options=[
                {"label": "Yes", "value": "yes"},
                {"label": "No", "value": "no"},
            ],
            expected_rate=2,
            ttl_days=90,
            business_importance=0.95,
        ),
        "odor": FacetConfig(
            question_text="Did the room have any unpleasant smell, such as smoke or mold?",
            options=[
                {"label": "No unpleasant smell", "value": "no_odor"},
                {"label": "Smoke smell", "value": "smoke"},
                {"label": "Mold / musty smell", "value": "mold"},
                {"label": "Other unpleasant smell", "value": "other_odor"},
            ],
            expected_rate=1,
            ttl_days=90,
            business_importance=0.9,
        ),
    },

    "ROOM_EXPERIENCE": {
        "hair_dryer": FacetConfig(
            question_text="Was a hair dryer provided?",
            options=[
                {"label": "Yes", "value": "yes"},
                {"label": "No", "value": "no"},
            ],
            expected_rate=1,
            ttl_days=365,
            business_importance=0.45,
        ),
        "body_wash": FacetConfig(
            question_text="Was body wash provided?",
            options=[
                {"label": "Yes", "value": "yes"},
                {"label": "No", "value": "no"},
            ],
            expected_rate=1,
            ttl_days=365,
            business_importance=0.4,
        ),
        "water_bottles": FacetConfig(
            question_text="Were complimentary bottles of water provided?",
            options=[
                {"label": "Yes", "value": "yes"},
                {"label": "No", "value": "no"},
                {"label": "Not sure", "value": "unknown"},
            ],
            expected_rate=1,
            ttl_days=180,
            business_importance=0.5,
        ),
        "toiletries": FacetConfig(
            question_text="Were disposable toiletries and a comb provided?",
            options=[
                {"label": "Yes", "value": "yes"},
                {"label": "No", "value": "no"},
                {"label": "Partially", "value": "partial"},
            ],
            expected_rate=1,
            ttl_days=365,
            business_importance=0.45,
        ),
    },

    "BED_SLEEP": {
        "pillow_count": FacetConfig(
            question_text="How many pillows were provided in the room?",
            options=[
                {"label": "1", "value": "1"},
                {"label": "2", "value": "2"},
                {"label": "3+", "value": "3_plus"},
                {"label": "Not sure", "value": "unknown"},
            ],
            expected_rate=1,
            ttl_days=365,
            business_importance=0.35,
        ),
        "pillow_options": FacetConfig(
            question_text="Were alternative pillow options available, such as latex or down pillows?",
            options=[
                {"label": "Yes", "value": "yes"},
                {"label": "No", "value": "no"},
                {"label": "Not sure", "value": "unknown"},
            ],
            expected_rate=1,
            ttl_days=365,
            business_importance=0.35,
        ),
        "turndown_service": FacetConfig(
            question_text="Was turndown service available?",
            options=[
                {"label": "Yes", "value": "yes"},
                {"label": "No", "value": "no"},
                {"label": "Not sure", "value": "unknown"},
            ],
            expected_rate=1,
            ttl_days=365,
            business_importance=0.3,
        ),
        "light_blocking": FacetConfig(
            question_text="Did the curtains block enough light at night or early in the morning?",
            options=[
                {"label": "Yes", "value": "good"},
                {"label": "No", "value": "poor"},
            ],
            expected_rate=1,
            ttl_days=180,
            business_importance=0.7,
        ),
    },

    "NOISE": {
        "external_noise": FacetConfig(
            question_text="Could you hear noise from the hallway, nearby rooms, or outside?",
            options=[
                {"label": "Quiet enough", "value": "quiet"},
                {"label": "Some noise", "value": "some_noise"},
                {"label": "Too noisy", "value": "too_noisy"},
            ],
            expected_rate=2,
            ttl_days=120,
            business_importance=0.9,
        ),
        "hvac_noise": FacetConfig(
            question_text="Was the air conditioning or heating too noisy?",
            options=[
                {"label": "Not noisy", "value": "quiet"},
                {"label": "A bit noisy", "value": "some_noise"},
                {"label": "Too noisy", "value": "too_noisy"},
            ],
            expected_rate=1,
            ttl_days=180,
            business_importance=0.75,
        ),
    },

    "ROOM_INFRA": {
        "lighting": FacetConfig(
            question_text="Was the lighting bright enough?",
            options=[
                {"label": "Yes", "value": "good"},
                {"label": "No", "value": "poor"},
            ],
            expected_rate=1,
            ttl_days=240,
            business_importance=0.55,
        ),
        "hvac_working": FacetConfig(
            question_text="Did the air conditioning or heating work properly?",
            options=[
                {"label": "Yes", "value": "working"},
                {"label": "No", "value": "not_working"},
            ],
            expected_rate=2,
            ttl_days=120,
            business_importance=0.9,
        ),
        "wifi_available": FacetConfig(
            question_text="Did this hotel offer Wi‑Fi?",
            options=[
                {"label": "Yes", "value": "yes"},
                {"label": "No", "value": "no"},
            ],
            expected_rate=1,
            ttl_days=180,
            business_importance=0.8,
        ),
        "wifi_fee": FacetConfig(
            question_text="Did Wi‑Fi require an extra fee?",
            options=[
                {"label": "Free", "value": "included"},
                {"label": "Extra fee", "value": "surcharge"},
                {"label": "No Wi‑Fi", "value": "not_available"},
                {"label": "Not sure", "value": "unknown"},
            ],
            expected_rate=1,
            ttl_days=180,
            business_importance=0.85,
        ),
    },

    "ROOM_SERVICE": {
        "breakfast_included": FacetConfig(
            question_text="Was breakfast included in the rate?",
            options=[
                {"label": "Included", "value": "included"},
                {"label": "Cost extra", "value": "surcharge"},
                {"label": "No breakfast", "value": "not_available"},
                {"label": "Not sure", "value": "unknown"},
            ],
            expected_rate=2,
            ttl_days=120,
            business_importance=0.95,
        ),
        "dietary_options": FacetConfig(
            question_text="Were there options for children or guests with dietary restrictions?",
            options=[
                {"label": "Yes", "value": "yes"},
                {"label": "No", "value": "no"},
                {"label": "Not sure", "value": "unknown"},
            ],
            expected_rate=1,
            ttl_days=180,
            business_importance=0.6,
        ),
        "late_food": FacetConfig(
            question_text="Were room service or late-night food options available?",
            options=[
                {"label": "Yes", "value": "yes"},
                {"label": "No", "value": "no"},
                {"label": "Not sure", "value": "unknown"},
            ],
            expected_rate=1,
            ttl_days=180,
            business_importance=0.65,
        ),
    },

    "HOTEL_INFRA": {
        "elevator": FacetConfig(
            question_text="Does the hotel have an elevator?",
            options=[
                {"label": "Yes", "value": "yes"},
                {"label": "No", "value": "no"},
                {"label": "Not sure", "value": "unknown"},
            ],
            expected_rate=1,
            ttl_days=365,
            business_importance=0.5,
        ),
        "luggage_storage": FacetConfig(
            question_text="Does the hotel offer luggage storage?",
            options=[
                {"label": "Yes", "value": "yes"},
                {"label": "No", "value": "no"},
                {"label": "Not sure", "value": "unknown"},
            ],
            expected_rate=1,
            ttl_days=365,
            business_importance=0.55,
        ),
        "shuttle": FacetConfig(
            question_text="Does the hotel provide a shuttle to the airport or major theme parks, and is there an extra charge?",
            options=[
                {"label": "Yes, free", "value": "available_included"},
                {"label": "Yes, costs extra", "value": "available_surcharge"},
                {"label": "No shuttle", "value": "not_available"},
                {"label": "Not sure", "value": "unknown"},
            ],
            expected_rate=2,
            ttl_days=120,
            business_importance=0.9,
        ),
        "public_transport": FacetConfig(
            question_text="Are there public transportation stops near the hotel?",
            options=[
                {"label": "Yes", "value": "yes"},
                {"label": "No", "value": "no"},
                {"label": "Not sure", "value": "unknown"},
            ],
            expected_rate=1,
            ttl_days=240,
            business_importance=0.6,
        ),
        "nearby_restaurants": FacetConfig(
            question_text="What are the restaurants like near the hotel?",
            options=[
                {"label": "Convenient / good variety", "value": "good"},
                {"label": "Limited options", "value": "limited"},
                {"label": "Not good", "value": "poor"},
                {"label": "Didn't try them", "value": "not_applicable"},
            ],
            expected_rate=1,
            ttl_days=180,
            business_importance=0.55,
        ),
    },
}