# API Contract
### The sacred document. Never change anything here without telling all members first.

---

## WebSocket — Chat Endpoint

```
WS /ws/chat/{session_id}?domain={banking|ecommerce}
```

### Client Sends (one message per turn)
```json
{ "message": "What is your return policy?" }
```

### Server Sends (required order every turn)

| Type | When | Shape |
|---|---|---|
| `status` *(optional)* | During processing (Tier 1 UX) | `{ "type": "status", "content": "Searching knowledge base..." }` |
| `token` | During streaming, one per chunk | `{ "type": "token", "content": "..." }` |
| `sources` | After stream ends | `{ "type": "sources", "content": [{ "file": "policy.pdf", "page": 4 }] }` |
| `confidence` | After `sources`, before `sentiment` | `{ "type": "confidence", "content": { "score": 0.72, "level": "medium" } }` |
| `sentiment` | After `confidence` | `{ "type": "sentiment", "content": "neutral" }` |
| `suggestions` *(optional)* | After sentiment, before done | `{ "type": "suggestions", "content": ["...", "..."] }` |
| `ticket` *(optional)* | After sentiment, before done | `{ "type": "ticket", "content": { "ticket_id": "1042", "status": "open" } }` |
| `done` | Last message of every turn | `{ "type": "done" }` |

**Ordering rules:**
- Required terminal sequence remains: `sources -> confidence -> sentiment -> done`
- `status` may appear before or during token streaming
- `suggestions`/`ticket` may appear only after `sentiment` and before `done`

### Sentiment Values
```
"positive"    ← user is happy or satisfied
"neutral"     ← default, no strong signal
"frustrated"  ← user is angry or repeatedly upset
```

### Domain Values
```
"banking"     ← loads banking FAISS index
"ecommerce"   ← loads ecommerce FAISS index
```

### Full Example Exchange
```
Client → { "message": "What is your refund policy?" }

Server → { "type": "token",     "content": "Our " }
Server → { "type": "token",     "content": "refund " }
Server → { "type": "token",     "content": "policy " }
Server → { "type": "token",     "content": "allows..." }
Server → { "type": "sources",   "content": [{ "file": "return_policy.pdf", "page": 4 }] }
Server → { "type": "confidence", "content": { "score": 0.72, "level": "medium" } }
Server → { "type": "sentiment", "content": "neutral" }
Server → { "type": "done" }
```

---

## REST — Voice Endpoint

```
POST /api/voice
Content-Type: multipart/form-data
```

### Request
```
Body: audio (binary file field)
      Format: webm or wav blob from browser MediaRecorder
```

### Response
```json
{ "transcript": "What is your return policy?" }
```

### Frontend Flow After This Call
1. Receive transcript string
2. Display in text input field
3. Auto-submit through WebSocket as a normal text message

---

## Internal Function Contracts
### (For M3 — these are the functions you call, don't touch internals)

### RAG Pipeline
```python
# Location: backend/rag/pipeline.py
# Owner: M1

async def query(
    message: str,       # user's message text
    domain: str,        # "banking" or "ecommerce"
    history: list       # list of {"role": "user"|"assistant", "content": str}
) -> AsyncGenerator[str, None]:
    # yields string tokens one by one
    # after iteration: access .sources, .confidence, and .sentiment on the pipeline object
```

### Usage in WebSocket handler
```python
async for token in pipeline.query(message, domain, history):
    await websocket.send_json({"type": "token", "content": token})

await websocket.send_json({"type": "sources",   "content": pipeline.last_sources})
await websocket.send_json({"type": "confidence", "content": pipeline.last_confidence})
await websocket.send_json({"type": "sentiment", "content": pipeline.last_sentiment})
await websocket.send_json({"type": "done"})
```

### Memory
```python
# Location: backend/agent/memory.py
# Owner: M3

def get_history(session_id: str) -> list:
    # returns list of {"role": ..., "content": ...} dicts

def add_turn(session_id: str, role: str, content: str) -> None:
    # role is "user" or "assistant"

def clear(session_id: str) -> None:
    # called when domain switches
```

### STT Provider
```python
# Location: backend/providers/stt/__init__.py
# Owner: M1 (M3 just calls it)

provider = get_stt_provider()
transcript: str = await provider.transcribe(audio_bytes: bytes)
```

---

## Change Rules

- Any change to this file must be announced in the group chat before committing
- If you add a new WebSocket message type, update the mock server the same day
- Never add fields to existing message shapes without discussing first — frontend breaks silently
- Version this file if shapes change: add a comment at the top with date and what changed
