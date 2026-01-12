from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Iterable
from urllib.parse import urlparse

import requests
from youtube_transcript_api import YouTubeTranscriptApi

from app.settings import settings

API_BASE = "https://www.googleapis.com/youtube/v3"


def _resolve_channel_id(channel_url: str) -> str | None:
    if "/channel/" in channel_url:
        return channel_url.split("/channel/")[-1].split("/")[0]
    if "@" in channel_url:
        handle = channel_url.split("@")[-1].strip("/")
        resp = requests.get(
            f"{API_BASE}/search",
            params={
                "key": settings.youtube_api_key,
                "q": handle,
                "type": "channel",
                "part": "snippet",
                "maxResults": 1,
            },
            timeout=20,
        )
        if resp.status_code != 200:
            return None
        data = resp.json().get("items", [])
        if not data:
            return None
        return data[0]["snippet"]["channelId"]
    return None


def _fetch_transcript(video_id: str) -> str:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([chunk["text"] for chunk in transcript])
    except Exception:
        return "transcript unavailable"


def fetch_videos(channels: Iterable[str]) -> list[dict]:
    if not settings.youtube_api_key:
        return []
    items: list[dict] = []
    for channel_url in channels:
        channel_id = _resolve_channel_id(channel_url)
        if not channel_id:
            continue
        resp = requests.get(
            f"{API_BASE}/search",
            params={
                "key": settings.youtube_api_key,
                "channelId": channel_id,
                "part": "snippet",
                "order": "date",
                "maxResults": 10,
            },
            timeout=20,
        )
        if resp.status_code != 200:
            continue
        for entry in resp.json().get("items", []):
            if entry.get("id", {}).get("kind") != "youtube#video":
                continue
            video_id = entry["id"]["videoId"]
            snippet = entry["snippet"]
            url = f"https://www.youtube.com/watch?v={video_id}"
            transcript = _fetch_transcript(video_id)
            dedupe_hash = hashlib.sha256(f"yt-{video_id}".encode()).hexdigest()
            items.append(
                {
                    "source_type": "youtube",
                    "title": snippet.get("title"),
                    "url": url,
                    "author": snippet.get("channelTitle"),
                    "published_at": snippet.get("publishedAt"),
                    "excerpt": snippet.get("description"),
                    "content": transcript,
                    "dedupe_hash": dedupe_hash,
                    "metadata": {"channel": channel_url},
                    "ingested_at": datetime.utcnow().isoformat(),
                }
            )
    return items
