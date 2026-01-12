from pathlib import Path
import yaml


WATCHLIST_PATH = Path("config/watchlist.yaml")


def load_watchlist() -> dict:
    if not WATCHLIST_PATH.exists():
        return {"people": [], "orgs": [], "rss_feeds": []}
    with WATCHLIST_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def save_watchlist(data: dict) -> None:
    WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with WATCHLIST_PATH.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=True)


def add_watchlist_entry(entry: dict) -> None:
    data = load_watchlist()
    entry_type = entry.get("entry_type", "person")
    if entry_type == "rss":
        data.setdefault("rss_feeds", []).append({"name": entry.get("name"), "url": entry.get("rss_url")})
    elif entry_type == "org":
        data.setdefault("orgs", []).append(
            {
                "name": entry.get("name"),
                "x_handle": entry.get("x_handle"),
                "website": entry.get("website"),
            }
        )
    else:
        data.setdefault("people", []).append(
            {
                "name": entry.get("name"),
                "lab": entry.get("lab"),
                "x_handle": entry.get("x_handle"),
                "website": entry.get("website"),
                "youtube_channel": entry.get("youtube_channel"),
            }
        )
    save_watchlist(data)


def flatten_watchlist(data: dict) -> list[dict]:
    entries: list[dict] = []
    for person in data.get("people", []):
        entries.append(
            {
                "name": person.get("name"),
                "entry_type": "person",
                "lab": person.get("lab"),
                "x_handle": person.get("x_handle"),
                "website": person.get("website"),
                "youtube_channel": person.get("youtube_channel"),
            }
        )
    for org in data.get("orgs", []):
        entries.append(
            {
                "name": org.get("name"),
                "entry_type": "org",
                "lab": org.get("name"),
                "x_handle": org.get("x_handle"),
                "website": org.get("website"),
            }
        )
    for feed in data.get("rss_feeds", []):
        entries.append(
            {
                "name": feed.get("name"),
                "entry_type": "rss",
                "rss_url": feed.get("url"),
            }
        )
    return entries


def all_x_handles(data: dict) -> list[str]:
    handles = []
    for group in (data.get("people", []), data.get("orgs", [])):
        for entry in group:
            handle = entry.get("x_handle")
            if handle:
                handles.append(handle)
    return handles


def all_youtube_channels(data: dict) -> list[str]:
    channels = []
    for person in data.get("people", []):
        channel = person.get("youtube_channel")
        if channel:
            channels.append(channel)
    return channels


def all_websites(data: dict) -> list[str]:
    sites = []
    for group in (data.get("people", []), data.get("orgs", [])):
        for entry in group:
            website = entry.get("website")
            if website:
                sites.append(website)
    return sites


def all_rss_feeds(data: dict) -> list[str]:
    feeds = []
    for feed in data.get("rss_feeds", []):
        url = feed.get("url")
        if url:
            feeds.append(url)
    return feeds
