from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Iterable

import requests

from app.settings import settings

API_BASE = "https://www.googleapis.com/customsearch/v1"


def search_web(queries: Iterable[str]) -> list[dict]:
    if not settings.google_cse_api_key or not settings.google_cse_cx:
        return []
    items: list[dict] = []
    for query in queries:
        resp = requests.get(
            API_BASE,
            params={
                "key": settings.google_cse_api_key,
                "cx": settings.google_cse_cx,
                "q": query,
                "num": 5,
            },
            timeout=20,
        )
        if resp.status_code != 200:
            continue
        for entry in resp.json().get("items", []):
            url = entry.get("link")
            if not url:
                continue
            dedupe_hash = hashlib.sha256(f"web-{url}".encode()).hexdigest()
            items.append(
                {
                    "source_type": "web",
                    "title": entry.get("title"),
                    "url": url,
                    "author": entry.get("displayLink"),
                    "published_at": entry.get("pagemap", {})
                    .get("metatags", [{}])[0]
                    .get("article:published_time"),
                    "excerpt": entry.get("snippet"),
                    "content": None,
                    "dedupe_hash": dedupe_hash,
                    "metadata": {"query": query},
                    "ingested_at": datetime.utcnow().isoformat(),
                }
            )
    return items
