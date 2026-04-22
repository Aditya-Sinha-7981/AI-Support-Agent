from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from agent.memory import add_turn, clear, get_history
from agent.router import route
from rag.pipeline import pipeline

router = APIRouter()

VALID_DOMAINS = {"banking", "ecommerce"}
_session_domains: dict[str, str] = {}


async def _send_turn_end(
    websocket: WebSocket, *, sources: list | None = None, sentiment: str = "neutral"
) -> None:
    await websocket.send_json({"type": "sources", "content": sources or []})
    await websocket.send_json({"type": "sentiment", "content": sentiment})
    await websocket.send_json({"type": "done"})


@router.websocket("/ws/chat/{session_id}")
async def chat(websocket: WebSocket, session_id: str):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "").strip()
            if not message:
                await websocket.send_json(
                    {"type": "token", "content": "Please send a non-empty message."}
                )
                await _send_turn_end(websocket)
                continue

            # 1. Domain handling
            domain = websocket.query_params.get("domain", "banking")
            if domain not in VALID_DOMAINS:
                domain = "banking"
            last_domain = _session_domains.get(session_id)
            if last_domain and last_domain != domain:
                clear(session_id)
            _session_domains[session_id] = domain

            target = route(message)
            if target == "empty":
                await websocket.send_json(
                    {"type": "token", "content": "Please send a non-empty message."}
                )
                await _send_turn_end(websocket)
                continue
            if target == "handoff":
                response = (
                    "I can help with policy and support questions here. "
                    "If you need a human agent, please share your issue details and I will guide next steps."
                )
                await websocket.send_json({"type": "token", "content": response})
                add_turn(session_id, "user", message)
                add_turn(session_id, "assistant", response)
                await _send_turn_end(websocket, sentiment="neutral")
                continue

            # 2. Memory (before pipeline)
            history = get_history(session_id)
            add_turn(session_id, "user", message)

            # 3. Pipeline call
            full_response = ""
            try:
                async for token in pipeline.query(message, domain, history):
                    full_response += token

                    await websocket.send_json({
                        "type": "token",
                        "content": token
                    })

                # 4. Sources → sentiment → done (API contract order)
                await _send_turn_end(
                    websocket,
                    sources=pipeline.last_sources,
                    sentiment=pipeline.last_sentiment,
                )
            except Exception:  # noqa: BLE001
                fallback = (
                    "I could not process that request right now. "
                    "Please verify backend setup and try again."
                )
                full_response = fallback
                await websocket.send_json({"type": "token", "content": fallback})
                await _send_turn_end(websocket)

            add_turn(session_id, "assistant", full_response)

    except WebSocketDisconnect:
        _session_domains.pop(session_id, None)
