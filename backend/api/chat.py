# Owner: M3
# WebSocket endpoint — /ws/chat/{session_id}

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from rag.pipeline import pipeline
from agent import memory

router = APIRouter()

@router.websocket("/ws/chat/{session_id}")
async def chat_endpoint(websocket: WebSocket, session_id: str):
    domain = websocket.query_params.get("domain", "banking")
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")

            history = memory.get_history(session_id)
            memory.add_turn(session_id, "user", message)

            async for token in pipeline.query(message, domain, history):
                await websocket.send_json({"type": "token", "content": token})

            await websocket.send_json({"type": "sources",   "content": pipeline.last_sources})
            await websocket.send_json({"type": "sentiment", "content": pipeline.last_sentiment})
            await websocket.send_json({"type": "done"})

            memory.add_turn(session_id, "assistant", "")  # M3: store full response here later

    except WebSocketDisconnect:
        pass
