from __future__ import annotations

from datetime import datetime
import logging

from app.content import normalize_published_at
from app.db import insert_item
from workers.content_extract import extract_excerpt
from workers.llm import LLMClient
from workers.relevance import normalize_text, rule_filter
from workers.scoring import rule_score
from workers.watchlist import (
    all_rss_feeds,
    all_x_handles,
    all_youtube_channels,
)
from workers.web_search import build_queries_from_watchlist, search_web
from workers.rss_ingest import ingest_feeds
from workers.x_client import fetch_x_posts
from workers.youtube_client import fetch_videos
from workers.watchlist import load_watchlist


LLM = LLMClient()
LOGGER = logging.getLogger(__name__)


def process_items(raw_items: list[dict]) -> int:
    inserted = 0
    for item in raw_items:
        published_at = normalize_published_at(item.get("published_at"))
        if not published_at:
            continue
        item["published_at"] = published_at
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
    watchlist_len = len(watchlist)
    x_items = fetch_x_posts(all_x_handles(watchlist))
    yt_items = fetch_videos(all_youtube_channels(watchlist))
    web_queries = build_queries_from_watchlist(watchlist)
    web_items = search_web(web_queries)
    rss_items = ingest_feeds(all_rss_feeds(watchlist))

    total = 0
    total += process_items(x_items)
    total += process_items(yt_items)
    total += process_items(web_items)
    total += process_items(rss_items)

    fetched_count = len(x_items) + len(yt_items) + len(web_items) + len(rss_items)
    LOGGER.info(
        "ingest_summary watchlist_len=%s queries_len=%s fetched_count=%s inserted_count=%s",
        watchlist_len,
        len(web_queries),
        fetched_count,
        total,
    )

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "inserted": total,
        "sources": {
            "x": len(x_items),
            "youtube": len(yt_items),
            "web": len(web_items),
            "rss": len(rss_items),
        },
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_ingestion(load_watchlist())
