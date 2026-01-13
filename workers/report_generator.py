from __future__ import annotations

from datetime import datetime, timedelta
import argparse
from pathlib import Path

from markdown import markdown
from weasyprint import HTML

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
            summary = item.get("summary") or ""
            excerpt = item.get("excerpt") or ""
            lines.append(f"- 中文摘要: {summary or '（无）'}")
            lines.append(f"- 英文摘录: {excerpt or '（无）'}")
            lines.append(f"- 原文链接: {item.get('url')}")
            lines.append("")
    return "\n".join(lines)


def build_html(markdown_content: str) -> str:
    html_body = markdown(markdown_content)
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <style>
      body {{
        font-family: "Noto Sans CJK SC", "Noto Sans CJK", "Noto Sans", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
        line-height: 1.6;
        color: #111827;
        margin: 32px;
      }}
      h1, h2, h3 {{
        color: #0f172a;
      }}
      a {{
        color: #2563eb;
      }}
      ul {{
        padding-left: 1.2rem;
      }}
    </style>
  </head>
  <body>
    {html_body}
  </body>
</html>
"""


def write_report(items: list[dict]) -> dict:
    reports_dir = Path(settings.data_dir) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    markdown_content = generate_markdown(items)
    md_path = reports_dir / f"report_{timestamp}.md"
    md_path.write_text(markdown_content, encoding="utf-8")

    html_path = reports_dir / f"report_{timestamp}.html"
    html_content = build_html(markdown_content)
    html_path.write_text(html_content, encoding="utf-8")

    pdf_path = reports_dir / f"report_{timestamp}.pdf"
    pdf_error = None
    try:
        HTML(string=html_content).write_pdf(str(pdf_path))
    except Exception as exc:
        pdf_error = f"PDF generation failed: {exc}"
        pdf_path = None

    return {
        "markdown": str(md_path),
        "html": str(html_path),
        "pdf": str(pdf_path) if pdf_path else None,
        "pdf_error": pdf_error,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate reports from ingested items.")
    parser.add_argument("--days", type=int, default=7, help="Number of days to include in the report.")
    parser.add_argument(
        "--format",
        choices=["md", "pdf", "html"],
        default="md",
        help="Output format to print to stdout.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    items = fetch_items(days=args.days)
    report_paths = write_report(items)
    if args.format == "pdf":
        if not report_paths["pdf"]:
            raise SystemExit(report_paths.get("pdf_error") or "PDF generation failed.")
        print(report_paths["pdf"])
        return
    if args.format == "html":
        print(report_paths["html"])
        return
    print(report_paths["markdown"])


if __name__ == "__main__":
    main()
