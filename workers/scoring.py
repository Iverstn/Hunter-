from datetime import datetime, timezone

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
        try:
            published_dt = datetime.fromisoformat(published_at)
            if published_dt.tzinfo is None:
                published_dt = published_dt.replace(tzinfo=timezone.utc)
            else:
                published_dt = published_dt.astimezone(timezone.utc)
            now = datetime.now(timezone.utc)
            age_hours = (now - published_dt).total_seconds() / 3600
            score += max(0.0, 2.0 - age_hours / 24)
        except ValueError:
            pass
    return round(score, 2)
