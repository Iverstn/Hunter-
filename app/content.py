from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.dates import combine_date_utc, parse_datetime, utc_now
from app.settings import settings


def normalize_published_at(value: str | None, *, now: datetime | None = None) -> str | None:
    parsed = parse_datetime(value)
    if not parsed:
        return None
    now = now or utc_now()
    min_date = combine_date_utc(settings.content_min_date)
    max_age_cutoff = now - timedelta(days=settings.content_max_age_days)
    if parsed < min_date or parsed < max_age_cutoff:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return parsed.isoformat()
