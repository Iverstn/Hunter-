from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Iterable

from app.settings import settings


DEFAULT_DB_PATH = Path("/app/data/radar.db")


def _resolve_db_path(db_path: str | Path) -> Path:
    path = Path(db_path)
    if path.exists():
        return path
    fallback = Path(settings.data_dir) / "radar.db"
    return fallback if fallback.exists() else path


def _ensure_schema(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            entry_type TEXT NOT NULL,
            lab TEXT,
            x_handle TEXT,
            website TEXT,
            youtube_channel TEXT,
            rss_url TEXT,
            created_at TEXT NOT NULL
        )
        """
    )


def load_watchlist(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    path = _resolve_db_path(db_path)
    if not path.exists():
        return []
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    _ensure_schema(cursor)
    rows = cursor.execute(
        """
        SELECT name, lab, x_handle, website, youtube_channel, rss_url
        FROM watchlist_entries
        ORDER BY name
        """
    ).fetchall()
    conn.close()
    return [
        {
            "name": row["name"],
            "lab": row["lab"],
            "x_handle": row["x_handle"],
            "website": row["website"],
            "youtube_channel": row["youtube_channel"],
            "rss_url": row["rss_url"],
        }
        for row in rows
    ]


def add_watchlist_entry(entry: dict, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    path = _resolve_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    _ensure_schema(cursor)
    cursor.execute(
        """
        INSERT INTO watchlist_entries
        (name, entry_type, lab, x_handle, website, youtube_channel, rss_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry.get("name"),
            entry.get("entry_type", "person"),
            entry.get("lab"),
            entry.get("x_handle"),
            entry.get("website"),
            entry.get("youtube_channel"),
            entry.get("rss_url"),
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def all_x_handles(entries: Iterable[dict]) -> list[str]:
    return [entry["x_handle"] for entry in entries if entry.get("x_handle")]


def all_youtube_channels(entries: Iterable[dict]) -> list[str]:
    return [entry["youtube_channel"] for entry in entries if entry.get("youtube_channel")]


def all_websites(entries: Iterable[dict]) -> list[str]:
    return [entry["website"] for entry in entries if entry.get("website")]


def all_rss_feeds(entries: Iterable[dict]) -> list[str]:
    return [entry["rss_url"] for entry in entries if entry.get("rss_url")]
