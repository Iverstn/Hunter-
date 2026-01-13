from __future__ import annotations

import hashlib
from datetime import datetime
import logging
from typing import Iterable

import requests

from app.content import normalize_published_at
from app.db import insert_item
from app.settings import settings
from workers.watchlist import all_websites, all_x_handles, load_watchlist

API_BASE = "https://www.googleapis.com/customsearch/v1"
LOGGER = logging.getLogger(__name__)


def build_queries_from_watchlist(watchlist: list[dict]) -> list[str]:
    return [*all_websites(watchlist), *all_x_handles(watchlist)]


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


def run_web_search() -> dict:
    watchlist = load_watchlist()
    queries = build_queries_from_watchlist(watchlist)
    items = search_web(queries)
    inserted = 0
    for item in items:
        published_at = normalize_published_at(item.get("published_at"))
        if not published_at:
            continue
        item["published_at"] = published_at
        if insert_item(item):
            inserted += 1
    LOGGER.info(
        "web_search_summary watchlist_len=%s queries_len=%s fetched_count=%s inserted_count=%s",
        len(watchlist),
        len(queries),
        len(items),
        inserted,
    )
    return {
        "watchlist_len": len(watchlist),
        "queries_len": len(queries),
        "fetched_count": len(items),
        "inserted_count": inserted,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_web_search()
