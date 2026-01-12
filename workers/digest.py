from __future__ import annotations

from datetime import datetime, timedelta

from app.db import get_connection
from app.settings import settings
from workers.llm import LLMClient

LLM = LLMClient()


def fetch_top_items(limit: int = 12) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    since = datetime.utcnow() - timedelta(days=1)
    rows = cursor.execute(
        """
        SELECT * FROM items
        WHERE ingested_at >= ?
        ORDER BY score DESC, published_at DESC
        LIMIT ?
        """,
        (since.isoformat(), limit),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def build_digest_html(items: list[dict]) -> str:
    parts = ["<h2>AI Signal Radar - Morning Digest</h2>"]
    for item in items:
        summary = item.get("summary") or item.get("excerpt") or ""
        analysis = item.get("analysis") or ""
        parts.append(
            f"<div style='margin-bottom:16px'>"
            f"<strong>{item['title']}</strong><br>"
            f"<em>{item.get('source_type')} | {item.get('author') or ''}</em><br>"
            f"<p>{summary}</p>"
            f"<p>{analysis}</p>"
            f"<a href='{settings.base_url}/items/{item['id']}'>View on dashboard</a>"
            f"</div>"
        )
    return "\n".join(parts)


def build_digest_text(items: list[dict]) -> str:
    lines = ["AI Signal Radar - Morning Digest"]
    for item in items:
        lines.append(f"- {item['title']} ({item.get('source_type')})")
        lines.append(f"  {item.get('summary') or item.get('excerpt') or ''}")
        lines.append(f"  {settings.base_url}/items/{item['id']}")
    return "\n".join(lines)
