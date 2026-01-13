from __future__ import annotations

from datetime import date, datetime, time, timezone

from dateutil import parser


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        parsed = parser.isoparse(value)
    except (ValueError, TypeError):
        try:
            parsed = parser.parse(value)
        except (ValueError, TypeError):
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def combine_date_utc(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)
