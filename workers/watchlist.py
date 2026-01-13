from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any

import yaml


WATCHLIST_PATH = Path("config/watchlist.yaml")


def load_watchlist(db_path: str | Path = "/app/data/radar.db") -> list[dict[str, Any]]:
    path = Path(db_path)
    if not path.exists():
        return []
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT name, entry_type, lab, x_handle, website, youtube_channel, rss_url
            FROM watchlist_entries
            ORDER BY name
            """
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()
    return [dict(row) for row in rows]


def load_watchlist_yaml() -> dict:
    if not WATCHLIST_PATH.exists():
        return {"people": [], "orgs": [], "rss_feeds": []}
    with WATCHLIST_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def save_watchlist(data: dict) -> None:
    WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with WATCHLIST_PATH.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=True)


def add_watchlist_entry(entry: dict, db_path: str | Path = "/app/data/radar.db") -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO watchlist_entries
            (name, entry_type, lab, x_handle, website, youtube_channel, rss_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                entry.get("name"),
                entry.get("entry_type", "person"),
                entry.get("lab"),
                entry.get("x_handle"),
                entry.get("website"),
                entry.get("youtube_channel"),
                entry.get("rss_url"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def flatten_watchlist(data: dict) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for person in data.get("people", []):
        entries.append(
            {
                "name": person.get("name"),
                "entry_type": "person",
                "lab": person.get("lab"),
                "x_handle": person.get("x_handle"),
                "website": person.get("website"),
                "youtube_channel": person.get("youtube_channel"),
            }
        )
    for org in data.get("orgs", []):
        entries.append(
            {
                "name": org.get("name"),
                "entry_type": "org",
                "lab": org.get("name"),
                "x_handle": org.get("x_handle"),
                "website": org.get("website"),
            }
        )
    for feed in data.get("rss_feeds", []):
        entries.append(
            {
                "name": feed.get("name"),
                "entry_type": "rss",
                "rss_url": feed.get("url"),
            }
        )
    return entries


def all_x_handles(entries: list[dict[str, Any]]) -> list[str]:
    return [entry["x_handle"] for entry in entries if entry.get("x_handle")]


def all_youtube_channels(entries: list[dict[str, Any]]) -> list[str]:
    return [entry["youtube_channel"] for entry in entries if entry.get("youtube_channel")]


def all_websites(entries: list[dict[str, Any]]) -> list[str]:
    return [entry["website"] for entry in entries if entry.get("website")]


def all_rss_feeds(entries: list[dict[str, Any]]) -> list[str]:
    return [entry["rss_url"] for entry in entries if entry.get("rss_url")]
