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


if __name__ == "__main__":
    from workers.ingest import process_items
    from workers.watchlist import all_rss_feeds, load_watchlist

    watchlist = load_watchlist()
    feeds = all_rss_feeds(watchlist)
    items = ingest_feeds(feeds)
    inserted = process_items(items)
    print(f"[rss_ingest] feeds={len(feeds)} fetched={len(items)} inserted={inserted}")
