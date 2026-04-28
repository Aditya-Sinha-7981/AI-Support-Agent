from __future__ import annotations

from collections import deque
from typing import Any, Deque

MAX_SESSION_TURNS = 16

# session_id -> deque[turn]
# A "turn" is a dict with required keys: role, content
# Optional keys: ts (float), sentiment (str), sources (list[dict]), ticket (dict)
sessions: dict[str, Deque[dict[str, Any]]] = {}


def get_history(session_id: str, max_turns: int = 8) -> list[dict[str, Any]]:
    """Return up to the last `max_turns` messages for a session."""
    history = sessions.get(session_id)
    if not history:
        return []
    if max_turns <= 0:
        return []
    return list(history)[-max_turns:]


def add_turn(
    session_id: str,
    role: str,
    content: str,
    meta: dict[str, Any] | None = None,
) -> None:
    """Add a normalized user/assistant message to session history."""
    normalized_role = (role or "").strip().lower()
    if normalized_role not in {"user", "assistant"}:
        return

    normalized_content = (content or "").strip()
    if not normalized_content:
        return

    if session_id not in sessions:
        sessions[session_id] = deque(maxlen=MAX_SESSION_TURNS)

    turn: dict[str, Any] = {"role": normalized_role, "content": normalized_content}
    if isinstance(meta, dict) and meta:
        # Avoid overriding required fields.
        meta = {k: v for k, v in meta.items() if k not in {"role", "content"}}
        turn.update(meta)

    sessions[session_id].append(turn)


def clear(session_id: str) -> None:
    """Clear all conversation history for a session."""
    sessions.pop(session_id, None)