import asyncio
from fastapi import APIRouter, WebSocket
from agent.memory import get_history, add_turn
from agent.sentiment import detect_sentiment

router = APIRouter()

@router.websocket("/ws/chat/{session_id}")
async def chat(websocket: WebSocket, session_id: str):
    await websocket.accept()

    while True:
        try:
            # 1. receive message
            data = await websocket.receive_json()
            message = data.get("message", "")

            # 2. get history
            history = get_history(session_id)

            # 3. detect sentiment
            sentiment = await detect_sentiment(message)

            # 4. build response
            full_response = f"You said: {message} | History count: {len(history)}"

            collected = ""

            # 5. stream tokens
            for word in full_response.split():
                token = word + " "
                collected += token

                await websocket.send_json({
                    "type": "token",
                    "content": token
                })

                await asyncio.sleep(0.1)

            # 6. send sentiment
            await websocket.send_json({
                "type": "sentiment",
                "content": sentiment
            })

            # 7. send done
            await websocket.send_json({
                "type": "done"
            })

            # 8. save memory
            add_turn(session_id, "user", message)
            add_turn(session_id, "assistant", collected)

        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "content": str(e)
            })
            break