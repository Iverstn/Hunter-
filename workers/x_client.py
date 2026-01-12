from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Iterable

import requests

from app.settings import settings

API_BASE = "https://api.twitter.com/2"


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.x_api_bearer_token}"}


def _user_id(handle: str) -> str | None:
    resp = requests.get(f"{API_BASE}/users/by/username/{handle}", headers=_headers(), timeout=20)
    if resp.status_code != 200:
        return None
    data = resp.json()
    return data.get("data", {}).get("id")


def fetch_x_posts(handles: Iterable[str]) -> list[dict]:
    if not settings.x_api_bearer_token:
        if settings.x_scrape_fallback:
            return []
        return []
    items: list[dict] = []
    for handle in handles:
        user_id = _user_id(handle)
        if not user_id:
            continue
        resp = requests.get(
            f"{API_BASE}/users/{user_id}/tweets",
            headers=_headers(),
            params={
                "tweet.fields": "created_at,author_id,referenced_tweets",
                "max_results": 20,
            },
            timeout=20,
        )
        if resp.status_code != 200:
            continue
        data = resp.json().get("data", [])
        for tweet in data:
            content = tweet.get("text", "")
            url = f"https://x.com/{handle}/status/{tweet.get('id')}"
            published_at = tweet.get("created_at")
            dedupe_hash = hashlib.sha256(f"x-{tweet.get('id')}".encode()).hexdigest()
            items.append(
                {
                    "source_type": "x",
                    "title": content[:120],
                    "url": url,
                    "author": handle,
                    "published_at": published_at,
                    "excerpt": content,
                    "content": content,
                    "dedupe_hash": dedupe_hash,
                    "metadata": {"handle": handle, "raw": tweet},
                    "ingested_at": datetime.utcnow().isoformat(),
                }
            )
    return items
