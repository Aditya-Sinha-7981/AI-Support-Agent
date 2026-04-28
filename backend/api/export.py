from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from datetime import datetime

# Import your real memory fetcher
from agent.memory import get_history

# Initialize a new router specifically for session-related actions
router = APIRouter()

@router.get("/sessions/{session_id}/export", response_class=PlainTextResponse)
async def export_conversation(session_id: str):
    
    # Fetch the real history (Setting max_turns high to get the whole chat)
    history = get_history(session_id, max_turns=100)

    if not history:
        raise HTTPException(status_code=404, detail="Session not found or empty.")

    # Format the data as clean Plain Text
    export_text = "CONVERSATION AUDIT TRAIL\n"
    export_text += "========================================\n"
    export_text += f"Session ID:  {session_id}\n"
    export_text += f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    export_text += "========================================\n\n"

    for turn in history:
        # We only pull what we actually have in memory.py
        role = str(turn.get("role", "user")).capitalize()
        content = turn.get("content", "")
        sources = turn.get("sources", [])

        # Clean text layout (Removed the timestamp and sentiment!)
        export_text += f"{role}\n"
        export_text += f"{content}\n"
        
        if role == "Assistant" and sources:
            export_text += f"Sources Cited: {', '.join(sources)}\n"
        
        export_text += "----------------------------------------\n\n"

    headers = {
        "Content-Disposition": f'attachment; filename="chat_export_{session_id}.txt"'
    }
    
    return PlainTextResponse(content=export_text, headers=headers)