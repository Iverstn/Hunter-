from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Iterable

import feedparser


def ingest_feeds(feeds: Iterable[str]) -> list[dict]:
    items: list[dict] = []
    for feed_url in feeds:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries[:10]:
            url = entry.get("link")
            dedupe_hash = hashlib.sha256(f"rss-{url}".encode()).hexdigest()
            items.append(
                {
                    "source_type": "rss",
                    "title": entry.get("title"),
                    "url": url,
                    "author": entry.get("author"),
                    "published_at": entry.get("published"),
                    "excerpt": entry.get("summary"),
                    "content": None,
                    "dedupe_hash": dedupe_hash,
                    "metadata": {"feed": feed_url},
                    "ingested_at": datetime.utcnow().isoformat(),
                }
            )
    return items
