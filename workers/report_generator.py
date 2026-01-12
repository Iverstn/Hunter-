from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from markdown import markdown

from app.db import get_connection
from app.settings import settings
from workers.llm import LLMClient
from workers.relevance import TAG_RULES

LLM = LLMClient()


def fetch_items(days: int = 7) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    since = datetime.utcnow() - timedelta(days=days)
    rows = cursor.execute(
        "SELECT * FROM items WHERE ingested_at >= ? ORDER BY published_at DESC",
        (since.isoformat(),),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def generate_markdown(items: list[dict]) -> str:
    lines = ["# AI Signal Radar 阅读报告", ""]
    lines.append("## 执行摘要")
    lines.append("（自动生成）")
    lines.append("")

    tags = list(TAG_RULES.keys())
    for tag in tags:
        tagged_items = [item for item in items if tag in (item.get("tags") or "")]
        if not tagged_items:
            continue
        lines.append(f"## {tag}")
        for item in tagged_items:
            lines.append(f"### {item['title']}")
            lines.append(f"- 来源: {item.get('source_type')} | 作者: {item.get('author')} | 日期: {item.get('published_at')}")
            summary = item.get("summary") or item.get("excerpt") or ""
            lines.append(f"- 中文摘要: {summary}")
            lines.append(f"- 原文链接: {item.get('url')}")
            lines.append("")
    return "\n".join(lines)


def write_report(items: list[dict]) -> dict:
    reports_dir = Path(settings.data_dir) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    markdown_content = generate_markdown(items)
    md_path = reports_dir / f"report_{timestamp}.md"
    md_path.write_text(markdown_content, encoding="utf-8")

    html_path = reports_dir / f"report_{timestamp}.html"
    html_path.write_text(markdown(markdown_content), encoding="utf-8")

    pdf_path = reports_dir / f"report_{timestamp}.pdf"
    try:
        from weasyprint import HTML

        HTML(string=markdown(markdown_content)).write_pdf(str(pdf_path))
    except Exception:
        pdf_path = None

    return {
        "markdown": str(md_path),
        "html": str(html_path),
        "pdf": str(pdf_path) if pdf_path else None,
    }
