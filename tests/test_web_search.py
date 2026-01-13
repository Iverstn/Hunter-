import importlib
from datetime import datetime, timedelta, timezone


def test_web_search_inserts_only_recent_items(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from app import settings as settings_module

    importlib.reload(settings_module)
    from app import db as db_module

    importlib.reload(db_module)
    from app import content as content_module
    from app import dates as dates_module

    importlib.reload(content_module)
    from workers import web_search as web_search_module

    importlib.reload(web_search_module)

    db_module.init_db()

    fixed_now = datetime(2025, 11, 10, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(content_module, "utc_now", lambda: fixed_now)

    items = [
        {
            "source_type": "web",
            "title": "Fresh ISO",
            "url": "https://example.com/fresh-iso",
            "author": "example.com",
            "published_at": "2025-11-09T10:00:00Z",
            "excerpt": "Fresh item",
            "content": None,
            "dedupe_hash": "hash-fresh-iso",
            "metadata": {"query": "test"},
            "ingested_at": fixed_now.isoformat(),
        },
        {
            "source_type": "web",
            "title": "Fresh RFC822",
            "url": "https://example.com/fresh-rfc822",
            "author": "example.com",
            "published_at": "Sat, 08 Nov 2025 15:08:15 GMT",
            "excerpt": "Fresh item",
            "content": None,
            "dedupe_hash": "hash-fresh-rfc822",
            "metadata": {"query": "test"},
            "ingested_at": fixed_now.isoformat(),
        },
        {
            "source_type": "web",
            "title": "Too Old",
            "url": "https://example.com/old",
            "author": "example.com",
            "published_at": "2025-10-30T10:00:00Z",
            "excerpt": "Old item",
            "content": None,
            "dedupe_hash": "hash-old",
            "metadata": {"query": "test"},
            "ingested_at": fixed_now.isoformat(),
        },
        {
            "source_type": "web",
            "title": "Unparseable",
            "url": "https://example.com/unparseable",
            "author": "example.com",
            "published_at": "not-a-date",
            "excerpt": "Bad item",
            "content": None,
            "dedupe_hash": "hash-unparseable",
            "metadata": {"query": "test"},
            "ingested_at": fixed_now.isoformat(),
        },
    ]

    monkeypatch.setattr(web_search_module, "load_watchlist", lambda: [])
    monkeypatch.setattr(web_search_module, "search_web", lambda queries: items)

    result = web_search_module.run_web_search()
    assert result["inserted_count"] == 2

    conn = db_module.get_connection()
    cursor = conn.cursor()
    rows = cursor.execute("SELECT published_at FROM items").fetchall()
    conn.close()

    published = [dates_module.parse_datetime(row[0]) for row in rows]
    assert all(value is not None for value in published)

    min_published = min(published)
    assert min_published >= datetime(2025, 11, 1, tzinfo=timezone.utc)
    assert min_published >= fixed_now - timedelta(days=7)

    for value in rows:
        assert value[0].endswith("+00:00")
