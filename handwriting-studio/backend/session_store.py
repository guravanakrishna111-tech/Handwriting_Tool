from __future__ import annotations

import time
from typing import Any, Dict


SESSION_TTL_SECONDS = 3600
sessions: Dict[str, Dict[str, Any]] = {}


def cleanup_sessions() -> None:
    now = time.time()
    expired = [sid for sid, data in sessions.items() if now - data.get("created_at", now) > SESSION_TTL_SECONDS]
    for sid in expired:
        sessions.pop(sid, None)


def get_session(session_id: str) -> Dict[str, Any]:
    cleanup_sessions()
    session = sessions.get(session_id)
    if not session:
        raise KeyError("Session not found or expired.")
    session["last_used"] = time.time()
    return session

