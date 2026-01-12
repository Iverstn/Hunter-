import pytest

pytest.importorskip("yaml")

from workers.watchlist import load_watchlist


def test_watchlist_load():
    data = load_watchlist()
    assert "people" in data
    assert len(data.get("people", [])) > 0
