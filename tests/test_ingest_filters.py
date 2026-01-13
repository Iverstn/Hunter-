import importlib
from datetime import datetime, timezone


def test_ingestion_filters_published_at(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from app import settings as settings_module

    importlib.reload(settings_module)
    from app import db as db_module

    importlib.reload(db_module)
    from app import content as content_module

    importlib.reload(content_module)
    from workers import ingest as ingest_module

    importlib.reload(ingest_module)

    db_module.init_db()

    fixed_now = datetime(2025, 11, 10, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(content_module, "utc_now", lambda: fixed_now)

    raw_items = [
        {
            "source_type": "x",
            "title": "AI fresh",
            "url": "https://example.com/fresh",
            "author": "alice",
            "published_at": "2025-11-09T10:00:00Z",
            "excerpt": "AI update",
            "content": "AI update",
            "dedupe_hash": "hash-fresh",
            "ingested_at": fixed_now.isoformat(),
        },
        {
            "source_type": "x",
            "title": "AI old",
            "url": "https://example.com/old",
            "author": "bob",
            "published_at": "2025-11-01T10:00:00Z",
            "excerpt": "AI update",
            "content": "AI update",
            "dedupe_hash": "hash-old",
            "ingested_at": fixed_now.isoformat(),
        },
        {
            "source_type": "x",
            "title": "AI missing",
            "url": "https://example.com/missing",
            "author": "cara",
            "published_at": None,
            "excerpt": "AI update",
            "content": "AI update",
            "dedupe_hash": "hash-missing",
            "ingested_at": fixed_now.isoformat(),
        },
    ]

    inserted = ingest_module.process_items(raw_items)
    assert inserted == 1

    conn = db_module.get_connection()
    cursor = conn.cursor()
    count = cursor.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    conn.close()
    assert count == 1
