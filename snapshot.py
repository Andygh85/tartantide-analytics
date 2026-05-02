"""
snapshot.py
Fetches YouTube stats and saves a timestamped snapshot.
Run daily via GitHub Actions.
"""

import os
import json
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

CHANNELS = {
    "Rapid Fire Five": os.getenv("CHANNEL_ID_RAPID_FIRE_FIVE"),
    "Born Today":      os.getenv("CHANNEL_ID_BORN_TODAY"),
    "Daily History":   os.getenv("CHANNEL_ID_DAILY_HISTORY"),
}

SNAPSHOTS_FILE = os.path.join(os.path.dirname(__file__), "data", "snapshots.json")


def fetch_channel_stats(channel_id: str) -> dict:
    url    = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "statistics,snippet",
        "id":   channel_id,
        "key":  YOUTUBE_API_KEY,
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data  = r.json()
    items = data.get("items", [])
    if not items:
        raise ValueError(f"No channel found for ID: {channel_id}")
    stats   = items[0]["statistics"]
    snippet = items[0]["snippet"]
    return {
        "title":       snippet.get("title", "Unknown"),
        "subscribers": int(stats.get("subscriberCount", 0)),
        "views":       int(stats.get("viewCount", 0)),
        "videos":      int(stats.get("videoCount", 0)),
    }


def load_snapshots() -> list:
    if not os.path.exists(SNAPSHOTS_FILE):
        return []
    with open(SNAPSHOTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_snapshots(snapshots: list):
    os.makedirs(os.path.dirname(SNAPSHOTS_FILE), exist_ok=True)
    with open(SNAPSHOTS_FILE, "w", encoding="utf-8") as f:
        json.dump(snapshots, f, indent=2)


def take_snapshot():
    snapshots = load_snapshots()
    timestamp = datetime.now(timezone.utc).isoformat()
    snapshot  = {
        "timestamp": timestamp,
        "channels":  {}
    }

    for name, channel_id in CHANNELS.items():
        if not channel_id:
            print(f"  Skipping {name} — no channel ID")
            continue
        try:
            stats = fetch_channel_stats(channel_id)
            snapshot["channels"][name] = stats
            print(f"  OK {name}: {stats['subscribers']:,} subs, {stats['views']:,} views")
        except Exception as e:
            print(f"  FAILED {name}: {e}")

    snapshots.append(snapshot)

    if len(snapshots) > 60:
        snapshots = snapshots[-60:]

    save_snapshots(snapshots)
    print(f"\nSnapshot saved at {timestamp}")


if __name__ == "__main__":
    print("Taking YouTube stats snapshot...")
    take_snapshot()
