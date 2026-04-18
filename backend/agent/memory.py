from collections import deque

# Store all sessions
sessions = {}

def get_history(session_id: str, max_turns: int = 8):
    """
    Returns last few messages of a session
    """
    return list(sessions.get(session_id, deque(maxlen=max_turns)))

def add_turn(session_id: str, role: str, content: str):
    """
    Add a message to session history
    """
    if session_id not in sessions:
        sessions[session_id] = deque(maxlen=16)

    sessions[session_id].append({
        "role": role,
        "content": content
    })

def clear(session_id: str):
    """
    Clear all conversation history for a session
    """
    if session_id in sessions:
        del sessions[session_id]