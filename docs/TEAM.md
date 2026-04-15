# AI Support Agent — Team Breakdown & Collaboration Guide

---

## Team Overview

| Member | Machine | Role |
|---|---|---|
| You (Lead) | MacBook Pro M4 Pro, 24GB | Backend core — RAG, providers, LLM integration |
| 3rd Member | i5 8th gen, 16GB RAM | Backend plumbing — API layer, WebSocket, agent utilities |
| Windows Partner | Windows laptop | Frontend — all React components, UI, hooks |
| 4th Member | Any | PPT, pitch script, RAG documents, demo rehearsal |

---

## The Core Split Logic

You own anything where a bug is hard to debug or kills the whole system.
Others own things that are isolated, testable, and replaceable.

---

## Member 1 — You (Lead, Mac M4)

### You Own
- Project scaffold — folder structure, `config.py`, `.env.example`, `requirements.txt`, `.gitignore`
- Provider abstraction layer — all three base classes (LLM, STT, TTS) and all implementations
- RAG pipeline — `ingestor.py`, `retriever.py`, `pipeline.py`
- Gemini streaming integration (Build Steps 1 and 2)
- Mock server for Windows partner (Day 1, ~2-3 hours)
- Pipeline stub for 3rd member (Day 1, ~30 minutes)
- Sentiment logic
- Domain switcher backend logic
- Final wiring in `main.py`
- Integration debugging when real frontend hits real backend
- Tier 1 extras from EXTRAS.md if time allows

### Why You Own This
The provider pattern, RAG pipeline, and streaming are the three things most likely to have subtle bugs
that take hours to find. These are not tasks to delegate to lower-skill team members.

### Your `.env`
```
STT_PROVIDER=local
LLM_PROVIDER=gemini
TTS_PROVIDER=edge
```

---

## Member 2 — 3rd Member (i5 8th gen, 16GB)

### He Owns
- `api/chat.py` — WebSocket endpoint, receives messages, calls pipeline, streams tokens back
- `api/voice.py` — POST endpoint, receives audio blob, calls STT provider, returns transcript
- `agent/memory.py` — conversation history per session, simple in-memory dict
- `agent/router.py` — intent classification, routes to RAG pipeline (lead scaffolds, he fills in)
- `main.py` — FastAPI app setup, registers routers, CORS middleware, startup events

### How He Works
He never touches RAG internals or provider implementations. He just calls functions you define.
You give him the contract:

> "Call `pipeline.query(message, domain, history)` — it returns an async generator of tokens.
> Iterate it and send each token over the WebSocket as `{"type": "token", "content": token}`"

He builds his entire WebSocket handler against a stub pipeline. When your real pipeline is ready,
you swap the stub. His code doesn't change at all.

### His `.env` (permanent — never change STT_PROVIDER)
```
STT_PROVIDER=deepgram
LLM_PROVIDER=gemini
TTS_PROVIDER=edge
```

His machine never runs faster-whisper. Deepgram is just an API call — zero local compute.
i5 8th gen + 16GB handles everything else comfortably.

### Testing
He tests via Postman or Thunder Client locally before any frontend integration happens.

---

## Member 3 — Windows Partner (Frontend)

### She Owns
- `ChatWindow.jsx` — message list, handles streaming token appending
- `MessageBubble.jsx` — single message with source citation card below it
- `VoiceInput.jsx` — mic button, waveform animation, transcript preview
- `SentimentBadge.jsx` — emoji indicator, top right, updates per turn
- `DomainSwitcher.jsx` — tab bar, clears chat on switch, sends domain to WebSocket
- `StreamingIndicator.jsx` — "Thinking..." animation while waiting
- `useWebSocket.js` — connection hook, handles all message types
- `useVoiceRecorder.js` — MediaRecorder API, sends audio blob to `/api/voice`

### How She Works Independently
She builds against the mock server from Day 1. The mock server has identical endpoint shapes
to the real backend. When you flip her to the ngrok URL, it works because the contract never changed.

She never needs to install the real backend. She never needs to wait for you to be online.

### Pointing to Your Server
During development: run the mock server locally (`uvicorn mock_server:app --reload`)
During integration: you share your ngrok URL, she changes one line in her config

---

## Member 4 — Non-Technical (PPT, Docs, Demo)

### She Owns
- **RAG documents** — realistic, well-structured PDFs for both domains
  - Banking: account opening requirements, loan policies, fee schedules, KYC docs, interest rates
  - E-commerce: return policy, shipping policy, product FAQs, warranty info, payment methods
- **Test question bank** — 20+ questions per domain that should have clear answers in the docs
  - Used by you to verify RAG is working correctly at Build Step 2
- **Edge case questions** — questions NOT in the docs, to verify bot says "I don't know" vs hallucinating
- **PPT and pitch deck** — the 60-second pitch from CORE.md, slide deck, architecture diagram
- **Demo rehearsal** — runs the demo script from CORE.md repeatedly with the team until smooth
- **Demo day operator** — runs the app during the presentation while lead pitches

Quality of RAG documents directly determines quality of answers. This is not a minor task.

---

## The WebSocket Contract (Sacred — Never Change Without Telling Everyone)

This is the agreed message format between backend and frontend.
Backend sends exactly these. Frontend handles exactly these. No surprises.

```
{ "type": "token",     "content": "..." }          ← streaming text token
{ "type": "sources",   "content": [{file, page}] } ← after stream ends
{ "type": "sentiment", "content": "neutral" }       ← neutral | frustrated | positive
{ "type": "done" }                                  ← stream complete
```

If you add a new message type (e.g. for escalation tickets or suggestions), update the mock server
the same day and tell Windows partner. This is the most common way she gets silently broken.

---

## How to Unblock Everyone on Day 1

You spend the first half of Day 1 doing these four things in order:

1. **Folder structure + `config.py`** — 1 hour
2. **`requirements.txt` + `.env.example`** — 30 mins
3. **Mock server for Windows partner** — 2 hours
4. **Pipeline stub for 3rd member** — 30 mins

Push to GitHub. Both of them pull. Both are fully unblocked. You go heads down on real backend.

### The Pipeline Stub (30 minutes of work, unblocks 3rd member entirely)
```python
# rag/pipeline.py — temporary stub
async def query(message: str, domain: str, history: list):
    # stub — yields fake tokens so 3rd member can build WebSocket handler
    for word in ["This ", "is ", "a ", "placeholder ", "response."]:
        yield word
```

### The Mock Server (2-3 hours of work, unblocks Windows partner entirely)
```python
# mock_server.py — she runs this locally, never needs your real backend
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.websocket("/ws/chat/{session_id}")
async def mock_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        for word in ["This ", "is ", "a ", "mock ", "response."]:
            await websocket.send_json({"type": "token", "content": word})
            await asyncio.sleep(0.05)
        await websocket.send_json({"type": "sources", "content": [{"file": "policy.pdf", "page": 4}]})
        await websocket.send_json({"type": "sentiment", "content": "neutral"})
        await websocket.send_json({"type": "done"})

@app.post("/api/voice")
async def mock_voice():
    return {"transcript": "What is your return policy?"}
```

---

## Serving Your Backend Remotely (ngrok)

Run your FastAPI server on your Mac. Run ngrok in front of it.
Everyone connects to the ngrok URL from anywhere — home, different network, mobile data.

```bash
# install ngrok once
brew install ngrok  # Mac

# run it
ngrok http 8000
# outputs something like: https://abc123.ngrok.io
# share this URL with the team
```

Your Mac needs to be on and ngrok running when they want to work against the real backend.
For the mock server phase this doesn't matter — they're fully local.

Cost: zero. All API calls (Gemini, Deepgram) happen on your machine.

---

## Git Workflow

Keep it simple. This is a hackathon, not a production codebase.

| Branch | Owner | Merges into |
|---|---|---|
| `main` | You | — |
| `backend` | You + 3rd member | `main` |
| `frontend` | Windows partner | `main` |

You own merges into `main`. No one pushes to `main` directly.

Sync frequency: at minimum after every completed build step. The danger zone is 3 days of
parallel work with no integration sync. Do quick check-ins daily.

Critical integration point: **Build Step 3 → 4** is when frontend first connects to real backend.
Do this together as a team, not async. Set aside 1-2 hours for it.

---

## Timeline

```
Day 1 (morning):   You — scaffold + mock server + pipeline stub → push to GitHub
Day 1 (afternoon): Everyone pulls, sets up env, confirms it runs

Day 2-4:   You — RAG pipeline, providers, Gemini streaming (Steps 1-2)
           Windows partner — ChatWindow, MessageBubble, useWebSocket against mock
           3rd member — memory.py, chat.py WebSocket handler against stub pipeline

Day 5-6:   Integration sync — Step 3+4 together
           His endpoints call your real pipeline
           Her frontend hits your ngrok URL for the first time

Day 7-8:   You — sentiment, domain switching, full wiring
           Windows partner — VoiceInput, SentimentBadge, DomainSwitcher
           3rd member — memory integrated into chat flow, voice endpoint

Day 9-10:  Full voice loop, TTS output, end to end testing
           4th member — RAG docs done, you ingest and test with her question bank

Day 11-12: Bug fixing, edge cases, UI polish

Day 13-14: Demo prep ONLY. No new features. Fix critical bugs only.
           Run demo script from CORE.md until everyone could do it in their sleep.
```

---

## The One Rule

If someone is blocked, you drop what you're doing and unblock them within the hour.
A stuck team member for a full day is a day of wasted parallel work.

Keep the mock server updated whenever you add a new WebSocket message type.
That's the #1 source of silent breakage on the frontend.
