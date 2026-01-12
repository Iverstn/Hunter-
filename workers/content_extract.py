from __future__ import annotations

import trafilatura


def extract_excerpt(url: str) -> str | None:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if not text:
            return None
        words = text.split()
        return " ".join(words[:400])
    except Exception:
        return None
