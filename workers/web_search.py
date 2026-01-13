from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Iterable
from urllib.parse import urlparse

import requests

from app.settings import settings

API_BASE = "https://www.googleapis.com/customsearch/v1"


def _domain_from_url(website: str) -> str:
    parsed = urlparse(website if "://" in website else f"//{website}")
    domain = parsed.netloc or parsed.path.split("/")[0]
    return domain.lstrip("www.") if domain else ""


def build_queries(entries: Iterable[dict]) -> list[str]:
    queries: list[str] = []
    for entry in entries:
        name = entry.get("name")
        lab = entry.get("lab")
        if not name and not lab:
            continue
        base = " ".join(filter(None, [name, lab]))
        website = entry.get("website")
        if website:
            domain = _domain_from_url(website)
            if domain:
                queries.append(f"{base} site:{domain}")
                continue
        queries.append(base)
    return queries


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


if __name__ == "__main__":
    from workers.ingest import process_items
    from workers.watchlist import load_watchlist

    watchlist = load_watchlist()
    queries = build_queries(watchlist)
    items = search_web(queries)
    inserted = process_items(items)
    print(
        "[web_search] watchlist_queries="
        f"{len(queries)} fetched={len(items)} inserted={inserted}"
    )
