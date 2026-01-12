import importlib
from pathlib import Path

import pytest

pytest.importorskip("pydantic_settings")


def test_init_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from app import settings as settings_module

    importlib.reload(settings_module)
    from app import db as db_module

    importlib.reload(db_module)
    db_module.init_db()
    db_path = Path(settings_module.settings.data_dir) / "radar.db"
    assert db_path.exists()
