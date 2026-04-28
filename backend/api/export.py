from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from agent.memory import get_history

router = APIRouter()


def _format_sources(sources: object) -> str:
    if not isinstance(sources, list) or not sources:
        return ""
    chunks: list[str] = []
    for item in sources:
        if isinstance(item, dict):
            file = str(item.get("file") or "unknown")
            page = item.get("page")
            if page is None:
                chunks.append(file)
            else:
                chunks.append(f"{file} (page {page})")
        else:
            chunks.append(str(item))
    return ", ".join(chunks)


@router.get("/api/sessions/{session_id}/export", response_class=PlainTextResponse)
async def export_conversation(session_id: str):
    history = get_history(session_id, max_turns=1000)
    if not history:
        raise HTTPException(status_code=404, detail="Session not found or empty.")

    export_lines: list[str] = []
    export_lines.append("CONVERSATION AUDIT TRAIL")
    export_lines.append("========================================")
    export_lines.append(f"Session ID:  {session_id}")
    export_lines.append(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    export_lines.append("========================================")
    export_lines.append("")

    for turn in history:
        role = str(turn.get("role", "user")).strip().lower()
        role_label = "Customer" if role == "user" else "Assistant"
        content = (turn.get("content") or "").strip()
        ts = turn.get("ts")
        sentiment = (turn.get("sentiment") or "").strip()
        sources_text = _format_sources(turn.get("sources"))

        header_bits: list[str] = [role_label]
        if isinstance(ts, (int, float)):
            header_bits.append(datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"))
        if role == "assistant" and sentiment:
            header_bits.append(f"sentiment={sentiment}")

        export_lines.append(" | ".join(header_bits))
        export_lines.append(content)
        if role == "assistant" and sources_text:
            export_lines.append(f"Sources: {sources_text}")
        export_lines.append("----------------------------------------")
        export_lines.append("")

    headers = {
        "Content-Disposition": f'attachment; filename="chat_export_{session_id}.txt"'
    }
    return PlainTextResponse(content="\n".join(export_lines).rstrip() + "\n", headers=headers)