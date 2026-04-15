from __future__ import annotations

import ast
import hashlib
import json
import re
from datetime import datetime, date
from typing import Any

from dateutil import parser


def parse_date_safe(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    try:
        return parser.parse(text).date()
    except Exception:
        return None


def parse_listish(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except Exception:
        pass
    return [text]


def parse_rating_overall(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    try:
        payload = json.loads(text)
        overall = payload.get("overall")
        return float(overall) if overall is not None else None
    except Exception:
        return None


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def make_review_id(property_id: str, acquisition_date: Any, review_title: str | None, review_text: str | None) -> str:
    raw = f"{property_id}|{acquisition_date}|{review_title or ''}|{review_text or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?;\n]+", text or "") if s.strip()]
