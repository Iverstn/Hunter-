from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

IMPORTANT_KEYWORDS = ["launch", "paper", "benchmark", "policy", "export control", "datacenter"]
SOURCE_WEIGHT = {"x": 1.0, "youtube": 1.2, "web": 1.1, "rss": 1.0}


def rule_score(item: dict) -> float:
    score = SOURCE_WEIGHT.get(item.get("source_type"), 1.0)
    title = (item.get("title") or "").lower()
    excerpt = (item.get("excerpt") or "").lower()
    for kw in IMPORTANT_KEYWORDS:
        if kw in title or kw in excerpt:
            score += 1.0
    published_at = item.get("published_at")
    if published_at:
        published_dt = _parse_published_at(published_at)
        if published_dt:
            age_hours = (datetime.now(timezone.utc) - published_dt).total_seconds() / 3600
            score += max(0.0, 2.0 - age_hours / 24)
    return round(score, 2)


def _parse_published_at(published_at: str) -> datetime | None:
    normalized = published_at.strip()
    try:
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        try:
            parsed = parsedate_to_datetime(normalized)
        except (TypeError, ValueError):
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
