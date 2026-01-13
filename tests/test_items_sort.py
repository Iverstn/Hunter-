import importlib
from datetime import datetime, timezone

from fastapi.testclient import TestClient


def test_items_sorted_by_published_at_desc(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from app import settings as settings_module

    importlib.reload(settings_module)
    from app import db as db_module

    importlib.reload(db_module)
    from app import main as main_module

    importlib.reload(main_module)

    monkeypatch.setattr(main_module, "run_cleanup", lambda: None)

    db_module.init_db()
    now = datetime(2025, 11, 10, 12, 0, tzinfo=timezone.utc)
    items = [
        {
            "source_type": "x",
            "title": "Newest item",
            "url": "https://example.com/new",
            "author": "alice",
            "published_at": (now.replace(hour=11)).isoformat(),
            "excerpt": "AI update",
            "content": "AI update",
            "dedupe_hash": "hash-new",
            "ingested_at": now.isoformat(),
        },
        {
            "source_type": "x",
            "title": "Older item",
            "url": "https://example.com/old",
            "author": "bob",
            "published_at": (now.replace(day=9, hour=9)).isoformat(),
            "excerpt": "AI update",
            "content": "AI update",
            "dedupe_hash": "hash-old",
            "ingested_at": now.isoformat(),
        },
    ]
    for item in items:
        assert db_module.insert_item(item)

    client = TestClient(main_module.app)
    login_response = client.post("/login", data={"password": settings_module.settings.dashboard_password})
    assert login_response.status_code in {200, 302}

    response = client.get("/items")
    assert response.status_code == 200
    text = response.text
    assert text.index("Newest item") < text.index("Older item")

    response = client.get("/items?sort=published_at_desc")
    assert response.status_code == 200
    text = response.text
    assert text.index("Newest item") < text.index("Older item")
