# Owner: M3
# Simple in-memory conversation history per session

from typing import List, Dict

_sessions: Dict[str, List[Dict]] = {}

def get_history(session_id: str) -> List[Dict]:
    return _sessions.get(session_id, [])

def add_turn(session_id: str, role: str, content: str) -> None:
    if session_id not in _sessions:
        _sessions[session_id] = []
    _sessions[session_id].append({"role": role, "content": content})

def clear(session_id: str) -> None:
    _sessions[session_id] = []
