# AI Customer Support Agent — Full Project Context
### Everything the AI assistant needs to know to continue this project from scratch.

---

## What We Are Building

An LLM-powered voice + text customer support agent with RAG (Retrieval-Augmented Generation). This is a hackathon project with a 2-week build window. The system answers domain-specific questions using a knowledge base, maintains conversation context across turns, detects user sentiment, and supports full voice input and output.

This is not a basic chatbot. The goal is a production-minded system that feels like a platform, not a demo.

---

## Team Context

- Team leader is experienced in Python, React, FastAPI, and AI/ML tooling
- Rest of team are beginners — the project will be largely vibe-coded
- Team leader uses a MacBook Pro M4 Pro (24GB RAM)
- Other teammates use Windows machines (no guaranteed Nvidia GPU)
- Cross-platform compatibility is a hard requirement — nothing that works only on Mac
- The goal is a clean, working, impressive demo — not maximum feature count

---

## The 4 Core USPs

These are what we pitch. These must work flawlessly before anything else is added.

1. **Voice-first full loop** — user speaks → sees live transcript → response streams in text → response is spoken back via TTS. Full end-to-end voice conversation.
2. **Multi-domain from one system** — same backend, same UI, switch between Banking and E-commerce with one click. Signals architectural maturity.
3. **Source-cited answers** — every response shows which document it came from (filename, page). Addresses the trust problem with AI.
4. **Sentiment-aware responses** — bot detects frustration and shifts its tone. An angry user gets empathetic language. A curious user gets informative language.

---

## API & Provider Strategy

### The Provider Pattern

Every external service is swappable via a single `.env` variable. No provider is hardcoded anywhere in the codebase. This means:
- Use free/local providers during development
- Swap to premium providers for final testing or demo day
- Zero code changes required — only `.env` changes

### Environment Variables
```
LLM_PROVIDER=gemini          # options: gemini | groq
STT_PROVIDER=local            # options: local | deepgram
TTS_PROVIDER=edge             # options: edge | elevenlabs
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
DEEPGRAM_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
```

### Provider Reference

| Service | Primary (Always Free) | Fallback (Credits) | Notes |
|---|---|---|---|
| LLM | Gemini 2.0 Flash | Groq (Llama 3.3 70B) | Both free. Groq is faster (~500 tok/s). |
| Embeddings | Gemini text-embedding-004 | — | Free, no fallback needed |
| STT | faster-whisper (local) | Deepgram Nova-2 | Local = always free. Deepgram = $200 credit on signup. |
| TTS | edge-tts (free) | ElevenLabs | edge-tts has zero limits. |
| Vector DB | FAISS (local) | — | Free, no infra, no external service |

### When to Use What
- **Daily development:** `STT_PROVIDER=local`, `LLM_PROVIDER=gemini`, `TTS_PROVIDER=edge`
- **Full integration testing:** `STT_PROVIDER=deepgram`
- **Demo day:** `STT_PROVIDER=deepgram`, `TTS_PROVIDER=edge` (or elevenlabs for better voice)

### Why Not OpenAI?
OpenAI has no meaningful free tier. Gemini 2.0 Flash is free (1500 req/day, 1M tokens/minute) and is the primary LLM. Groq is free with rate limits and serves as fallback.

---

## Tech Stack

| Layer | Tool | Reason |
|---|---|---|
| LLM | Gemini 2.0 Flash | Free, fast, high quality |
| LLM Fallback | Groq (Llama 3.3 70B) | Free, extremely fast |
| Embeddings | Gemini (`GEMINI_EMBEDDING_MODEL`) | Free, configurable via `.env` |
| RAG Framework | Direct pipeline (`faiss-cpu` + custom retriever) | Simpler, cross-platform, no LlamaIndex dependency |
| Vector DB | FAISS (local) | No infra, no external service, fast enough |
| STT Primary | faster-whisper (local) | Free, works on CPU, cross-platform |
| STT Fallback | Deepgram Nova-2 | Best latency for real demos |
| TTS | edge-tts | Free, no limits, decent voice quality |
| Backend | FastAPI | Async, streaming-native, LlamaIndex-friendly |
| Frontend | React + Tailwind | Fast to build, clean UI |
| Agent Flow | Simple sequential pipeline (`router -> rag -> stream`) | Keeps integration straightforward for hackathon pace |

### Why Not LangGraph?
LangGraph is the right tool for complex agent state machines but has a real learning curve. For vibe-coding beginners, it becomes spaghetti fast. Simple sequential LangChain chains give 80% of the capability with 20% of the complexity. This was a deliberate decision.

---

## Project Folder Structure

```
ai-support-agent/
│
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Reads .env, exposes settings object
│   ├── requirements.txt         # Pinned dependencies
│   ├── .env                     # Never commit this
│   ├── .env.example             # Commit this (no real keys)
│   │
│   ├── providers/               # THE SWAP LAYER
│   │   ├── llm/
│   │   │   ├── base.py          # Abstract base class
│   │   │   ├── gemini.py        # Gemini 2.0 Flash
│   │   │   └── groq.py          # Groq
│   │   ├── stt/
│   │   │   ├── base.py
│   │   │   ├── local_whisper.py # faster-whisper, CPU mode
│   │   │   └── deepgram.py      # Deepgram Nova-2 REST (not streaming)
│   │   └── tts/
│   │       ├── base.py
│   │       ├── edge_tts.py      # Always free
│   │       └── elevenlabs.py    # Credits only
│   │
│   ├── rag/
│   │   ├── ingestor.py          # Load docs → chunk → embed → save FAISS
│   │   ├── retriever.py         # Query FAISS → return top-K chunks + metadata
│   │   └── pipeline.py          # Full RAG: query → retrieve → inject → LLM → respond
│   │
│   ├── agent/
│   │   ├── router.py            # Intent classification, routes query
│   │   ├── memory.py            # Conversation history per session (in-memory)
│   │   └── sentiment.py         # Detects sentiment, returns label
│   │
│   ├── api/
│   │   ├── chat.py              # WebSocket /ws/chat/{session_id}
│   │   └── voice.py             # POST /api/voice — audio in, transcript out
│   │
│   └── data/
│       ├── documents/
│       │   ├── banking/         # PDFs, text files for banking domain
│       │   └── ecommerce/       # PDFs, text files for e-commerce domain
│       └── indexes/
│           ├── banking/         # FAISS index (auto-generated, gitignored)
│           └── ecommerce/       # FAISS index (auto-generated, gitignored)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx        # Message list with streaming
│   │   │   ├── MessageBubble.jsx     # Single message + source citation card
│   │   │   ├── VoiceInput.jsx        # Mic button + waveform + transcript
│   │   │   ├── SentimentBadge.jsx    # Emoji indicator, updates per turn
│   │   │   ├── DomainSwitcher.jsx    # Banking / E-commerce tab bar
│   │   │   └── StreamingIndicator.jsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js       # WebSocket connection + message handling
│   │   │   └── useVoiceRecorder.js   # MediaRecorder API (browser-side audio)
│   │   └── services/
│   │       └── api.js                # All fetch/WebSocket calls
│   └── package.json
```

---

## How Each System Works

### Provider Pattern (The Swap Layer)

Every provider has a base class defining the interface. Implementations fill it in. A factory function reads `.env` and returns the right implementation. The rest of the app never imports a provider directly.

```python
# providers/stt/base.py
from abc import ABC, abstractmethod

class BaseSTT(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes) -> str:
        pass

# providers/stt/__init__.py
def get_stt_provider():
    if settings.STT_PROVIDER == "deepgram":
        from .deepgram import DeepgramSTT
        return DeepgramSTT()
    from .local_whisper import LocalWhisperSTT
    return LocalWhisperSTT()
```

Same pattern for LLM and TTS. App calls `get_stt_provider().transcribe(audio)` and never thinks about which provider is active.

### faster-whisper Cross-Platform Rule
Always use `device="cpu", compute_type="int8"`. Never use GPU acceleration — it differs per platform (Metal on Mac, CUDA on Windows). CPU mode works identically everywhere and is fast enough.

```python
self.model = WhisperModel("medium", device="cpu", compute_type="int8")
```

### RAG Pipeline

**Ingestion (run once per domain):**
```
Load documents (PDF/TXT)
→ Split into chunks (512 tokens, 50 token overlap)
→ Embed each chunk with Gemini text-embedding-004
→ Store embeddings + metadata in FAISS
→ Save index to disk with faiss.write_index()
```

**Query (every user message):**
```
User query
→ Embed query with same model
→ FAISS search → top 4 most similar chunks
→ Each chunk carries: {source_file, page_number, chunk_text}
→ Inject into LLM prompt as context
→ LLM generates answer
→ Response includes source references sent to frontend
```

Critical: always call `faiss.write_index()` after ingestion. If skipped, the index resets on server restart.

### Conversation Memory

In-memory session store. Last 8 turns injected into every LLM prompt.

```python
sessions = {}  # session_id → deque of message dicts

def get_history(session_id: str) -> list:
    return list(sessions.get(session_id, []))

def add_turn(session_id: str, role: str, content: str):
    if session_id not in sessions:
        sessions[session_id] = deque(maxlen=16)
    sessions[session_id].append({"role": role, "content": content})
```

### Sentiment Detection

Current implementation uses a hybrid classifier for low latency and better edge-case quality.
It scores sentiment locally first and can optionally invoke an LLM fallback only when uncertain.
It returns API-contract-aligned values only: `positive`, `neutral`, or `frustrated`.

Result is used to:
1. Update the sentiment badge in the UI
2. Modify the system prompt tone for frustrated users

### API Endpoints

**WebSocket — Main Chat:**
```
WS /ws/chat/{session_id}?domain={banking|ecommerce}

Client sends:  { "message": "What is your refund policy?" }

Server sends (required terminal order):
  { "type": "status", "content": "Searching knowledge base..." }   ← optional Tier 1
  { "type": "token", "content": "Our " }          ← streaming
  { "type": "token", "content": "refund " }
  { "type": "token", "content": "policy..." }
  { "type": "sources", "content": [{file, page}] }
  { "type": "sentiment", "content": "neutral" }
  { "type": "suggestions", "content": ["...", "..."] }             ← optional Tier 1
  { "type": "ticket", "content": {"ticket_id": "1042"} }           ← optional Tier 1
  { "type": "done" }
```

**REST — Voice:**
```
POST /api/voice
Body: multipart/form-data audio blob (webm/wav from browser)
Response: { "transcript": "What is your refund policy?" }
```

Frontend gets transcript → submits through WebSocket as normal text message.

### Audio Capture Rule
Audio is always captured in the **browser via JavaScript MediaRecorder API**, never in Python. This eliminates pyaudio/sounddevice cross-platform hell entirely. The browser handles all OS-level audio.

---

## Frontend UI Layout

```
┌─────────────────────────────────────────────────┐
│  [Banking]  [E-commerce]          😐 Neutral     │
├─────────────────────────────────────────────────┤
│                                                 │
│  [Bot] Hello! How can I help you today?         │
│                                                 │
│       I want to know about the refund policy[Me]│
│                                                 │
│  [Bot] Our refund policy allows returns         │
│        within 30 days of purchase...            │
│        ┌──────────────────────────┐             │
│        │ 📄 Source: policy.pdf    │             │
│        │    Page 4                │             │
│        └──────────────────────────┘             │
│                                                 │
│  Searching knowledge base...  ← status line     │
│                                                 │
├─────────────────────────────────────────────────┤
│  🎙️ [Mic]   [Text input field]        [Send]    │
└─────────────────────────────────────────────────┘
```

**Key behaviors:**
- Responses stream token by token — no loading spinner then full dump
- Source citation cards appear below each bot response
- Sentiment badge updates after every user message
- Status line shows what agent is doing while processing
- Domain switch clears chat and loads new FAISS index
- Voice: click mic → waveform appears → click again to stop → transcript auto-submits → TTS plays response

---

## Cross-Platform Rules (Non-Negotiable)

| Rule | Reason |
|---|---|
| `pathlib.Path` for ALL file paths | Windows uses `\`, Mac uses `/` |
| Everyone on Python 3.11 or 3.12+ | 3.11 preferred; 3.12+ works with current stack |
| Everyone uses venv | No global pip installs |
| `requirements.txt` with unpinned versions | Avoids brittle pins across Mac/Windows for hackathon velocity |
| Audio capture in browser JS only | Avoids pyaudio platform issues |
| faster-whisper always `device="cpu", compute_type="int8"` | GPU differs per platform |
| `.env` — no spaces around `=`, no unnecessary quotes | Windows dotenv is stricter |

### Setup (Everyone Runs This)
```bash
git clone <repo-url>
cd ai-support-agent/backend
python -m venv venv

# Mac/Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
```

---

## Dependencies

```
# requirements.txt (backend)
fastapi
uvicorn[standard]
python-multipart
websockets
python-dotenv
pydantic-settings
numpy
faiss-cpu
pypdf
google-genai
groq
faster-whisper
edge-tts
httpx
aiofiles
```

---

## Build Order

Follow this strictly. Do not jump ahead. Each step must work before the next begins.

```
1. Gemini answers a hardcoded question in a Python script
   DONE WHEN: Streaming tokens appear in terminal

2. RAG pipeline works in isolation
   DONE WHEN: Ask a question about an uploaded PDF, get correct answer with source cited

3. FastAPI wraps RAG, WebSocket works
   DONE WHEN: Postman/Thunder Client receives streamed tokens

4. React frontend connects, text chat works
   DONE WHEN: Full text conversation works in browser

5. Conversation memory added
   DONE WHEN: Follow-up question ("what about its price?") gets correct contextual answer

6. Sentiment detection added
   DONE WHEN: Frustrated message → 😤 badge appears in UI

7. Voice input (STT) added
   DONE WHEN: Spoken question → correct text answer

8. Voice output (TTS) added
   DONE WHEN: Full voice loop works end to end

9. Domain switcher added
   DONE WHEN: Banking question only returns banking documents

10. UI polish
    DONE WHEN: You would be proud to screen-record this
```

---

## Demo Day Script

Practice this until it is smooth. Every hesitation costs points.

1. Open app. Banking domain selected. Type: *"What documents do I need to open a savings account?"* — show streaming response and source citation card.
2. Follow up: *"What about the minimum balance?"* — show context memory working.
3. Switch to E-commerce. Chat clears, knowledge base changes.
4. Use voice: click mic, say *"What is your return policy?"* — show waveform, transcript appearing, streaming response, TTS plays back.
5. Type: *"This is ridiculous, I've been waiting 3 weeks for my order"* — show 😤 badge, show empathetic response tone.
6. Point out source citation on any answer.

Total: ~3 minutes. Rehearse it.

---

## Known Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Voice breaks on demo day | Text chat is complete fallback. Never demo voice first. |
| Gemini rate limit during testing | Switch `LLM_PROVIDER=groq` in `.env` |
| Deepgram credits running low | Use `STT_PROVIDER=local` during dev, Deepgram only for real tests |
| FAISS index missing on restart | Ingestion script checks for index on startup, auto-rebuilds if missing |
| Windows path errors | All paths use `pathlib.Path`. Test on Windows in Week 1. |
| Venue internet down | Keep ollama + llama3.2:3b installed as emergency LLM fallback. `STT_PROVIDER=local` always works offline. |

---

## Bonus Features (Only After Core Is Complete)

Ordered by impact vs effort:

**Tier 1 (under a day each):**
- Escalation detection — if user is frustrated for 2+ turns, create a support ticket, show in UI
- Query rewriting — LLM rewrites vague queries before RAG search, improves retrieval quality
- Agent status line — "Searching knowledge base..." / "Generating response..." while processing
- Suggested follow-ups — 2-3 clickable question chips after each response
- Language auto-detection — add one line to system prompt, Gemini handles Hindi/English natively

**Tier 2 (2-3 days):**
- Admin document upload — drag-drop PDF, ingest live, immediately queryable. Best live demo moment.
- Confidence score — show green/yellow based on FAISS similarity score, bot acknowledges uncertainty
- Conversation export — download chat transcript with sources as text file

**Tier 3 (only if core is rock solid):**
- Analytics dashboard — total conversations, sentiment breakdown, most asked questions, Recharts
- Streaming TTS — speak response sentence by sentence as it generates, cuts latency dramatically
- Hybrid search — BM25 + FAISS + Reciprocal Rank Fusion, improves edge case retrieval

---

## Pitch Script (60 seconds)

> "Most support bots are search engines with a chat wrapper. Ours is different in four ways.
>
> First, it's voice-native — speak to it and hear responses back, end to end.
>
> Second, it's source-transparent — every answer cites the exact document it came from, which matters in regulated industries like banking.
>
> Third, it's emotionally intelligent — it tracks sentiment across a conversation and shifts its tone when a customer is frustrated.
>
> Fourth, it's domain-agnostic — the same system works for banking, e-commerce, or healthcare by switching the knowledge base.
>
> The architecture is also provider-agnostic — we can swap any component, LLM, STT, or TTS, without touching business logic. One environment variable. That's important for production systems."

---

## What This Project Is NOT

- Not using LangGraph (too complex for this team, deliberate decision)
- Not using OpenAI (no free tier)
- Not using MCP (solves a problem we don't have)
- Not using Redis (in-memory session store is sufficient for demo)
- Not using Pinecone (FAISS local is sufficient)
- Not capturing audio in Python (browser only)
- Not running LLM locally (API is faster and smarter, local only as emergency fallback)
