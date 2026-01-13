from __future__ import annotations

from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.db import (
    cleanup_old_items,
    get_item,
    init_db,
    list_suggested_people,
    list_watchlist,
    query_items,
    approve_suggested_person,
    upsert_watchlist,
)
from app.settings import settings
from workers.digest import build_digest_html, build_digest_text, fetch_top_items
from workers.ingest import run_ingestion
from workers.report_generator import fetch_items, write_report
from workers.send_email import send_email
from workers.watchlist import (
    add_watchlist_entry,
    flatten_watchlist,
    load_watchlist,
    load_watchlist_yaml,
)

app = FastAPI(title="AI Signal Radar")
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

scheduler = BackgroundScheduler(timezone=settings.timezone)


def require_login(request: Request) -> None:
    if not request.session.get("logged_in"):
        raise HTTPException(status_code=401)


def run_daily_digest() -> None:
    items = fetch_top_items(limit=12)
    if not items:
        return
    html_body = build_digest_html(items)
    text_body = build_digest_text(items)
    send_email("AI Signal Radar Morning Digest", html_body, text_body)


def run_hourly_ingest() -> None:
    watchlist = load_watchlist()
    run_ingestion(watchlist)


def run_cleanup() -> None:
    cleanup_old_items()


@app.on_event("startup")
async def startup_event() -> None:
    init_db()
    watchlist = load_watchlist()
    if not watchlist:
        legacy_watchlist = load_watchlist_yaml()
        legacy_entries = flatten_watchlist(legacy_watchlist)
        if legacy_entries:
            upsert_watchlist(legacy_entries)
    scheduler.add_job(run_hourly_ingest, "interval", hours=1)
    scheduler.add_job(run_daily_digest, "cron", hour=8, minute=30)
    scheduler.add_job(run_cleanup, "cron", hour=2, minute=0)
    scheduler.start()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    if not request.session.get("logged_in"):
        return RedirectResponse("/login")
    return RedirectResponse("/items")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request, password: str = Form(...)) -> RedirectResponse:
    if password != settings.dashboard_password:
        return TEMPLATES.TemplateResponse(
            "login.html", {"request": request, "error": "Invalid password"}, status_code=401
        )
    request.session["logged_in"] = True
    return RedirectResponse("/items", status_code=302)


@app.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


@app.get("/items", response_class=HTMLResponse)
async def items_view(request: Request, source: str | None = None, search: str | None = None, tags: str | None = None, min_score: float | None = None) -> HTMLResponse:
    require_login(request)
    filters = {
        "source_type": source,
        "search": search,
        "tags": tags,
        "min_score": min_score,
    }
    rows = query_items(filters)
    return TEMPLATES.TemplateResponse(
        "items.html",
        {"request": request, "items": rows, "filters": filters},
    )


@app.get("/items/{item_id}", response_class=HTMLResponse)
async def item_detail(request: Request, item_id: int) -> HTMLResponse:
    require_login(request)
    row = get_item(item_id)
    if not row:
        raise HTTPException(status_code=404)
    return TEMPLATES.TemplateResponse("item_detail.html", {"request": request, "item": row})


@app.get("/watchlist", response_class=HTMLResponse)
async def watchlist_view(request: Request) -> HTMLResponse:
    require_login(request)
    entries = list_watchlist()
    return TEMPLATES.TemplateResponse("watchlist.html", {"request": request, "entries": entries})


@app.post("/watchlist/add")
async def watchlist_add(
    request: Request,
    name: str = Form(...),
    entry_type: str = Form("person"),
    lab: str | None = Form(None),
    x_handle: str | None = Form(None),
    website: str | None = Form(None),
    youtube_channel: str | None = Form(None),
    rss_url: str | None = Form(None),
) -> RedirectResponse:
    require_login(request)
    add_watchlist_entry(
        {
            "name": name,
            "entry_type": entry_type,
            "lab": lab,
            "x_handle": x_handle,
            "website": website,
            "youtube_channel": youtube_channel,
            "rss_url": rss_url,
        }
    )
    return RedirectResponse("/watchlist", status_code=302)


@app.get("/suggested", response_class=HTMLResponse)
async def suggested_view(request: Request) -> HTMLResponse:
    require_login(request)
    entries = list_suggested_people()
    return TEMPLATES.TemplateResponse("suggested.html", {"request": request, "entries": entries})


@app.post("/suggested/approve")
async def suggested_approve(
    request: Request,
    suggested_id: int = Form(...),
    name: str = Form(...),
    x_handle: str | None = Form(None),
) -> RedirectResponse:
    require_login(request)
    add_watchlist_entry({"name": name, "entry_type": "person", "x_handle": x_handle})
    approve_suggested_person(suggested_id)
    return RedirectResponse("/suggested", status_code=302)


@app.post("/reports/generate", response_class=HTMLResponse)
async def generate_report(request: Request, days: int = Form(7)) -> HTMLResponse:
    require_login(request)
    items = fetch_items(days=days)
    report_paths = write_report(items)
    md_filename = Path(report_paths["markdown"]).name
    pdf_filename = Path(report_paths["pdf"]).name if report_paths["pdf"] else None
    return TEMPLATES.TemplateResponse(
        "report_links.html",
        {
            "request": request,
            "report_paths": report_paths,
            "days": days,
            "md_filename": md_filename,
            "pdf_filename": pdf_filename,
        },
    )


@app.get("/reports/download/{filename}")
async def download_report_file(request: Request, filename: str) -> FileResponse:
    require_login(request)

    reports_dir = (Path(settings.data_dir) / "reports").resolve()
    file_path = (reports_dir / filename).resolve()
    if not file_path.exists() or not file_path.is_relative_to(reports_dir):

    media_type = "application/octet-stream"
    if file_path.suffix == ".pdf":
        media_type = "application/pdf"
    elif file_path.suffix == ".md":
        media_type = "text/markdown"
    else:
        raise HTTPException(status_code=404)
    return FileResponse(file_path, media_type=media_type, filename=file_path.name)


@app.get("/report")
async def download_report(request: Request, days: int = 7, format: str = "md") -> FileResponse:
    require_login(request)
    items = fetch_items(days=days)
    report_paths = write_report(items)
    normalized_format = format.lower()
    if normalized_format == "pdf":
        if report_paths["pdf"]:
            pdf_path = Path(report_paths["pdf"])
            return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_path.name)
        error_message = report_paths.get("pdf_error") or "PDF generation failed; returning Markdown."
        md_path = Path(report_paths["markdown"])
        headers = {"X-Report-Error": error_message}
        return FileResponse(md_path, media_type="text/markdown", filename=md_path.name, headers=headers)
    md_path = Path(report_paths["markdown"])
    return FileResponse(md_path, media_type="text/markdown", filename=md_path.name)


@app.post("/ingest/run")
async def ingest_now(request: Request) -> RedirectResponse:
    require_login(request)
    run_hourly_ingest()
    return RedirectResponse("/items", status_code=302)
