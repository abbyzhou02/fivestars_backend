from __future__ import annotations

import hashlib
import re
from datetime import date, datetime


def normalize_whitespace(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


from datetime import datetime


from datetime import datetime
import pandas as pd


def parse_date_safe(v):

    if v is None:
        return None

    if isinstance(v, float) and pd.isna(v):
        return None

    s = str(v).strip()

    if not s:
        return None

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%Y/%m/%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except:
            pass

    try:
        return pd.to_datetime(s).date()
    except:
        return None


def parse_rating_overall(value: object) -> float | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        return None

    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None

    try:
        return float(match.group(0))
    except ValueError:
        return None


def make_review_id(
    property_id: str,
    acquisition_date: date | None,
    review_title: str | None,
    review_text: str | None,
) -> str:
    payload = "||".join(
        [
            property_id or "",
            acquisition_date.isoformat() if acquisition_date else "",
            normalize_whitespace(review_title),
            normalize_whitespace(review_text),
        ]
    )
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()
    return f"{property_id}_{digest}"
