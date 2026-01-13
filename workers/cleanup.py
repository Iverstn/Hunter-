from __future__ import annotations

import logging

from app.db import cleanup_old_items

LOGGER = logging.getLogger(__name__)


def run_cleanup() -> int:
    deleted = cleanup_old_items()
    LOGGER.info("cleanup_deleted=%s", deleted)
    return deleted


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_cleanup()
