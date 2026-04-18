from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from agent.memory import get_history, add_turn

# -----------------------------
# ✅ DUMMY PIPELINE (TEMP)
# -----------------------------
class DummyPipeline:
    def __init__(self):
        self.last_sources = [{"file": "demo.pdf", "page": 1}]
        self.last_sentiment = "neutral"

    async def query(self, message, domain, history):
        response = f"Dummy response for {domain}"

        for word in response.split():
            yield word + " "

        # simulate updated metadata
        self.last_sources = [{"file": f"{domain}.pdf", "page": 2}]
        self.last_sentiment = "neutral"


pipeline = DummyPipeline()


router = APIRouter()

VALID_DOMAINS = {"banking", "ecommerce"}

@router.websocket("/ws/chat/{session_id}")
async def chat(websocket: WebSocket, session_id: str):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "").strip()

            # -----------------------------
            # 1. Domain handling
            # -----------------------------
            domain = websocket.query_params.get("domain", "banking")
            if domain not in VALID_DOMAINS:
                domain = "banking"

            # -----------------------------
            # 2. Memory (before pipeline)
            # -----------------------------
            history = get_history(session_id)
            add_turn(session_id, "user", message)

            # -----------------------------
            # 3. Pipeline call
            # -----------------------------
            full_response = ""

            async for token in pipeline.query(message, domain, history):
                full_response += token

                await websocket.send_json({
                    "type": "token",
                    "content": token
                })

            # -----------------------------
            # 4. SEND SOURCES
            # -----------------------------
            await websocket.send_json({
                "type": "sources",
                "content": pipeline.last_sources
            })

            # -----------------------------
            # 5. SEND SENTIMENT
            # -----------------------------
            await websocket.send_json({
                "type": "sentiment",
                "content": pipeline.last_sentiment
            })

            # -----------------------------
            # 6. SEND DONE
            # -----------------------------
            await websocket.send_json({
                "type": "done"
            })

            # -----------------------------
            # 7. Save assistant response
            # -----------------------------
            add_turn(session_id, "assistant", full_response)

    except WebSocketDisconnect:
        pass