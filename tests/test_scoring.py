from datetime import datetime, timezone

from workers.scoring import rule_score


def test_rule_score_accepts_naive_published_at() -> None:
    published_at = datetime(2024, 1, 1, 12, 0, 0).isoformat()
    score = rule_score({"published_at": published_at})
    assert isinstance(score, float)


def test_rule_score_accepts_timezone_aware_published_at() -> None:
    published_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc).isoformat()
    score = rule_score({"published_at": published_at})
    assert isinstance(score, float)
