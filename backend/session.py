"""
session.py — In-memory multi-turn conversation session management.

Each session stores:
  - message history (for the LLM context window)
  - accumulated search filters (merged across turns)

Production note: Replace the in-memory dict with Redis (with TTL)
for horizontal scaling across multiple API instances.
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Session:
    session_id: str
    messages: list[dict[str, str]] = field(default_factory=list)
    # Accumulated filters from all prior turns
    active_filters: dict[str, Any] = field(default_factory=dict)


# In-process session store — swap for Redis in production
_sessions: dict[str, Session] = {}


def get_or_create(session_id: str | None) -> Session:
    if session_id and session_id in _sessions:
        return _sessions[session_id]
    sid = session_id or str(uuid.uuid4())
    session = Session(session_id=sid)
    _sessions[sid] = session
    return session


def delete_session(session_id: str) -> bool:
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


def merge_filters(existing: dict[str, Any], new_filters: dict[str, Any]) -> dict[str, Any]:
    """
    Merge new filter values from the latest turn into accumulated state.

    Rules:
    - None values in new_filters mean "user didn't mention this" → keep existing
    - Non-None values override (e.g., "make it blue" replaces the previous color)
    - Special key "clear_all" resets everything
    """
    if new_filters.get("clear_all"):
        return {}

    merged = dict(existing)
    for key, val in new_filters.items():
        if key == "clear_all":
            continue
        if val is not None:
            merged[key] = val

    return merged
