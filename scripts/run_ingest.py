from app.db import init_db, upsert_watchlist
from workers.ingest import run_ingestion
from workers.watchlist import flatten_watchlist, load_watchlist

if __name__ == "__main__":
    init_db()
    watchlist = load_watchlist()
    upsert_watchlist(flatten_watchlist(watchlist))
    result = run_ingestion(watchlist)
    print(result)
