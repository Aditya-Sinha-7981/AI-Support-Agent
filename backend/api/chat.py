from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from agent.memory import get_history, add_turn
from rag.pipeline import pipeline

router = APIRouter()

VALID_DOMAINS = {"banking", "ecommerce"}


@router.websocket("/ws/chat/{session_id}")
async def chat(websocket: WebSocket, session_id: str):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "").strip()

            # 1. Domain handling
            domain = websocket.query_params.get("domain", "banking")
            if domain not in VALID_DOMAINS:
                domain = "banking"

            # 2. Memory (before pipeline)
            history = get_history(session_id)
            add_turn(session_id, "user", message)

            # 3. Pipeline call
            full_response = ""

            async for token in pipeline.query(message, domain, history):
                full_response += token

                await websocket.send_json({
                    "type": "token",
                    "content": token
                })

            # 4. Sources → sentiment → done (API contract order)
            await websocket.send_json({
                "type": "sources",
                "content": pipeline.last_sources
            })

            await websocket.send_json({
                "type": "sentiment",
                "content": pipeline.last_sentiment
            })

            await websocket.send_json({
                "type": "done"
            })

            add_turn(session_id, "assistant", full_response)

    except WebSocketDisconnect:
        pass
