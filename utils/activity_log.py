from __future__ import annotations

import datetime
from typing import Optional

from utils import storage

STORE_NAME = "activity_log"
MAX_ENTRIES = 10000


def record(
    guild_id: int,
    user_id: int,
    category: str,
    summary: str,
    *,
    moderator_id: Optional[int] = None,
    channel_id: Optional[int] = None,
) -> None:
    """Καταγράφει ένα event ώστε να είναι αναζητήσιμο μέσω /find.

    category: "join_leave" | "roles" | "channels" | "messages" | "voice" | "moderation"
    """
    store = storage.get_store(STORE_NAME, {"entries": []})
    entries = store.setdefault("entries", [])

    entries.append({
        "guild_id": guild_id,
        "user_id": user_id,
        "category": category,
        "summary": summary,
        "moderator_id": moderator_id,
        "channel_id": channel_id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).timestamp(),
    })

    if len(entries) > MAX_ENTRIES:
        del entries[: len(entries) - MAX_ENTRIES]

    storage.save(STORE_NAME, store)


def search(guild_id: int, user_id: int, category: Optional[str] = None) -> list[dict]:
    store = storage.get_store(STORE_NAME, {"entries": []})
    entries = store.get("entries", [])
    results = [
        e for e in entries
        if e.get("guild_id") == guild_id
        and (e.get("user_id") == user_id or e.get("moderator_id") == user_id)
        and (category is None or e.get("category") == category)
    ]
    results.sort(key=lambda e: e.get("timestamp", 0), reverse=True)
    return results
