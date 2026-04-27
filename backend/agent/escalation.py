from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class _EscalationState:
    consecutive_frustrated: int = 0


_session_state: dict[str, _EscalationState] = {}
_session_tickets: dict[str, list[dict[str, Any]]] = {}


def _next_ticket_id() -> str:
    return uuid4().hex[:8].upper()


def _build_summary(user_message: str, assistant_reply: str) -> str:
    user = (user_message or "").strip()
    reply = (assistant_reply or "").strip()
    if not reply:
        return f"Customer reported: {user[:140]}"
    return f"Customer reported: {user[:120]} | Assistant replied: {reply[:120]}"


def maybe_create_ticket(
    session_id: str,
    *,
    sentiment: str,
    user_message: str,
    assistant_reply: str,
) -> dict[str, Any] | None:
    """
    Create an escalation ticket if user sentiment is frustrated for 2 consecutive turns.
    Creates a single ticket at the threshold and waits for sentiment to reset.
    """
    state = _session_state.setdefault(session_id, _EscalationState())

    if sentiment == "frustrated":
        state.consecutive_frustrated += 1
    else:
        state.consecutive_frustrated = 0
        return None

    if state.consecutive_frustrated != 2:
        return None

    ticket = {
        "ticket_id": _next_ticket_id(),
        "status": "open",
        "summary": _build_summary(user_message, assistant_reply),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _session_tickets.setdefault(session_id, []).append(ticket)
    return ticket


def get_tickets(session_id: str) -> list[dict[str, Any]]:
    return list(_session_tickets.get(session_id, []))
