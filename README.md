# AI Signal Radar (V0)

A minimal, end-to-end system that monitors a curated AI watchlist, ingests signals from X/YouTube/Web/RSS, scores and tags them, and serves:

- A daily buy-side style morning digest email (08:30 Asia/Singapore).
- A password-protected dashboard (English + 中文混合 UI).
- On-demand reading report (default last 7 days) in Markdown with optional PDF.

## Quickstart (Docker)

```bash
cp .env.example .env
# fill keys in .env

docker compose up --build
```

Open http://localhost:8000 and log in with `DASHBOARD_PASSWORD`.

## Environment Variables

See `.env.example` for the full list. Core settings:

- `DASHBOARD_PASSWORD`: password for login.
- `DEFAULT_EMAIL_RECIPIENT`: digest recipient.
- `X_API_BEARER_TOKEN`, `YOUTUBE_API_KEY`, `GOOGLE_CSE_API_KEY`, `GOOGLE_CSE_CX`: source APIs.
- `OPENAI_API_KEY`: optional LLM classifier and summaries.
- `SMTP_*`: Gmail SMTP for digest.

## Scheduling

The app runs a background scheduler:

- Hourly ingestion.
- Daily digest at 08:30 Asia/Singapore.
- Daily cleanup (90-day retention).

## Watchlist

Edit `config/watchlist.yaml` or use the Watchlist UI to add/remove people, orgs, websites, and RSS feeds. Restart the container after changes.

## Reports

In the dashboard, click “Generate report”. Files are written to `/data/reports` and downloaded as Markdown.

## Development (local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Notes

- If APIs are missing, ingestion silently skips those sources.
- X scraping fallback is a placeholder (toggle `X_SCRAPE_FALLBACK=true` for best-effort mode).
- Web scraping uses trafilatura and respects site availability. If extraction fails, metadata only is stored.
