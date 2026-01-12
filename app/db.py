import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from app.settings import settings

DB_PATH = Path(settings.data_dir) / "radar.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()
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
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            author TEXT,
            published_at TEXT,
            ingested_at TEXT NOT NULL,
            excerpt TEXT,
            content TEXT,
            summary TEXT,
            analysis TEXT,
            score REAL DEFAULT 0,
            tags TEXT,
            metadata_json TEXT,
            dedupe_hash TEXT UNIQUE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS item_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            FOREIGN KEY(item_id) REFERENCES items(id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS suggested_people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL,
            approved INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()


def upsert_watchlist(entries: Iterable[dict]) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchlist_entries")
    for entry in entries:
        cursor.execute(
            """
            INSERT INTO watchlist_entries
            (name, entry_type, lab, x_handle, website, youtube_channel, rss_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.get("name"),
                entry.get("entry_type"),
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


def insert_item(item: dict) -> int | None:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO items
            (source_type, title, url, author, published_at, ingested_at, excerpt, content,
             summary, analysis, score, tags, metadata_json, dedupe_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["source_type"],
                item["title"],
                item["url"],
                item.get("author"),
                item.get("published_at"),
                item.get("ingested_at", datetime.utcnow().isoformat()),
                item.get("excerpt"),
                item.get("content"),
                item.get("summary"),
                item.get("analysis"),
                item.get("score", 0.0),
                ",".join(item.get("tags", [])),
                json.dumps(item.get("metadata", {})),
                item.get("dedupe_hash"),
            ),
        )
        item_id = cursor.lastrowid
        for tag in item.get("tags", []):
            cursor.execute(
                "INSERT INTO item_tags (item_id, tag) VALUES (?, ?)",
                (item_id, tag),
            )
        conn.commit()
        return item_id
    except sqlite3.IntegrityError:
        conn.rollback()
        return None
    finally:
        conn.close()


def query_items(filters: dict) -> list[sqlite3.Row]:
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM items WHERE 1=1"
    params: list = []

    if filters.get("source_type"):
        query += " AND source_type = ?"
        params.append(filters["source_type"])
    if filters.get("min_score"):
        query += " AND score >= ?"
        params.append(filters["min_score"])
    if filters.get("start_date"):
        query += " AND published_at >= ?"
        params.append(filters["start_date"])
    if filters.get("end_date"):
        query += " AND published_at <= ?"
        params.append(filters["end_date"])
    if filters.get("tags"):
        query += " AND tags LIKE ?"
        params.append(f"%{filters['tags']}%")
    if filters.get("search"):
        query += " AND (title LIKE ? OR excerpt LIKE ? OR content LIKE ?)"
        params.extend([f"%{filters['search']}%"] * 3)

    query += " ORDER BY published_at DESC NULLS LAST, ingested_at DESC"
    rows = cursor.execute(query, params).fetchall()
    conn.close()
    return rows


def get_item(item_id: int) -> sqlite3.Row | None:
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    return row


def cleanup_old_items(days: int = 90) -> int:
    cutoff = datetime.utcnow() - timedelta(days=days)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE ingested_at < ?", (cutoff.isoformat(),))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def list_watchlist() -> list[sqlite3.Row]:
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM watchlist_entries ORDER BY name").fetchall()
    conn.close()
    return rows


def add_suggested_person(name: str, reason: str | None) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO suggested_people (name, reason, created_at, approved) VALUES (?, ?, ?, 0)",
        (name, reason, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def list_suggested_people() -> list[sqlite3.Row]:
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM suggested_people ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def approve_suggested_person(suggested_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE suggested_people SET approved = 1 WHERE id = ?", (suggested_id,))
    conn.commit()
    conn.close()
