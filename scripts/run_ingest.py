from app.db import init_db
from workers.ingest import run_ingestion
from workers.watchlist import load_watchlist

if __name__ == "__main__":
    init_db()
    watchlist = load_watchlist()
    result = run_ingestion(watchlist)
    print(result)
