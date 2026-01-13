from __future__ import annotations

from datetime import datetime

from app.db import insert_item
from workers.content_extract import extract_excerpt
from workers.llm import LLMClient
from workers.relevance import normalize_text, rule_filter
from workers.scoring import rule_score
from workers.watchlist import (
    all_rss_feeds,
    all_x_handles,
    all_youtube_channels,
    load_watchlist,
)
from workers.web_search import build_queries, search_web
from workers.rss_ingest import ingest_feeds
from workers.x_client import fetch_x_posts
from workers.youtube_client import fetch_videos


LLM = LLMClient()


def process_items(raw_items: list[dict]) -> int:
    inserted = 0
    for item in raw_items:
        text = normalize_text(" ".join(filter(None, [item.get("title"), item.get("excerpt"), item.get("content")])) )
        filter_result = rule_filter(text)
        if not filter_result.keep:
            continue
        if item.get("excerpt") is None and item["source_type"] in {"web", "rss"}:
            excerpt = extract_excerpt(item["url"])
            if excerpt:
                item["excerpt"] = excerpt
        item["tags"] = filter_result.tags
        item["score"] = rule_score(item)

        if LLM.enabled():
            llm_result = LLM.classify(text)
            item["summary"] = llm_result.get("summary")
            item["analysis"] = llm_result.get("analysis")
            item["score"] = item["score"] + llm_result.get("score_adjust", 0)

        item_id = insert_item(item)
        if item_id:
            inserted += 1
    return inserted


def run_ingestion(watchlist: list[dict]) -> dict:
    errors: dict[str, str] = {}
    fetched_counts: dict[str, int] = {}
    inserted_counts: dict[str, int] = {}

    x_handles = all_x_handles(watchlist)
    youtube_channels = all_youtube_channels(watchlist)
    web_queries = build_queries(watchlist)
    rss_feeds = all_rss_feeds(watchlist)

    watchlist_counts = {
        "x": len(x_handles),
        "youtube": len(youtube_channels),
        "web": len(web_queries),
        "rss": len(rss_feeds),
    }

    def _fetch(label: str, func) -> list[dict]:
        try:
            items = func()
        except Exception as exc:
            errors[label] = str(exc)
            print(f"[ingest] {label} fetch failed: {exc}")
            items = []
        fetched_counts[label] = len(items)
        return items

    def _process(label: str, items: list[dict]) -> int:
        try:
            inserted = process_items(items)
        except Exception as exc:
            errors[label] = str(exc)
            print(f"[ingest] {label} processing failed: {exc}")
            inserted = 0
        inserted_counts[label] = inserted
        return inserted

    x_items = _fetch("x", lambda: fetch_x_posts(x_handles))
    yt_items = _fetch("youtube", lambda: fetch_videos(youtube_channels))
    web_items = _fetch("web", lambda: search_web(web_queries))
    rss_items = _fetch("rss", lambda: ingest_feeds(rss_feeds))

    total = 0
    total += _process("x", x_items)
    total += _process("youtube", yt_items)
    total += _process("web", web_items)
    total += _process("rss", rss_items)

    print("[ingest] Watchlist counts:", watchlist_counts)
    print("[ingest] Fetched counts:", fetched_counts)
    print("[ingest] Inserted counts:", inserted_counts)
    if errors:
        print("[ingest] Errors:", errors)
    print(f"[ingest] Summary: inserted={total}")

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "inserted": total,
        "watchlist": watchlist_counts,
        "fetched": fetched_counts,
        "inserted_by_source": inserted_counts,
        "errors": errors,
    }


if __name__ == "__main__":
    run_ingestion(load_watchlist())
