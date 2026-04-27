"""
MOCK SERVER — for M2 (frontend) use only.
Run this locally: uvicorn mock_server:app --reload --port 8000
Has identical endpoint shapes to the real backend.
When M1's real backend is ready, M2 just changes the URL in her config. Nothing else changes.
"""

import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Mock Server — AI Support Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/chat/{session_id}")
async def mock_chat(websocket: WebSocket, session_id: str):
    domain = websocket.query_params.get("domain", "banking")
    await websocket.accept()

    while True:
        data = await websocket.receive_json()
        message = data.get("message", "")

        await websocket.send_json(
            {"type": "status", "content": "Searching knowledge base..."}
        )
        await asyncio.sleep(0.05)
        await websocket.send_json(
            {"type": "status", "content": "Generating response..."}
        )

        # Simulate streaming tokens
        mock_response = (
            f"This is a mock response for domain '{domain}'. "
            f"You asked: '{message}'. "
            "In the real app, this will be a streamed LLM answer with RAG context."
        )
        for word in mock_response.split():
            await websocket.send_json({"type": "token", "content": word + " "})
            await asyncio.sleep(0.05)

        # Sources
        await websocket.send_json({
            "type": "sources",
            "content": [
                {"file": "sample_policy.pdf", "page": 4},
                {"file": "faq_document.pdf", "page": 2}
            ]
        })

        # Sentiment — cycles through values so M2 can test all badge states
        sentiments = ["neutral", "positive", "frustrated"]
        mock_sentiment = sentiments[len(message) % 3]
        await websocket.send_json({"type": "sentiment", "content": mock_sentiment})
        await websocket.send_json(
            {
                "type": "suggestions",
                "content": [
                    "Can you explain this in simple terms?",
                    "What documents do I need?",
                    "Are there any fees for this?",
                ],
            }
        )
        if mock_sentiment == "frustrated":
            await websocket.send_json(
                {
                    "type": "ticket",
                    "content": {
                        "ticket_id": "MOCK-1042",
                        "status": "open",
                        "summary": "Customer is frustrated and requested escalation.",
                    },
                }
            )

        await websocket.send_json({"type": "done"})


@app.post("/api/voice")
async def mock_voice():
    # Always returns the same transcript so M2 can test the voice flow
    return {"transcript": "What is your return policy?"}


@app.get("/health")
async def health():
    return {"status": "mock server running"}
