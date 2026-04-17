# 🧠 AI Customer Support Agent — CORE BUILD
### The non-negotiable foundation. Everything here must work perfectly.

---

## 📌 Project Summary

We are building an **LLM-powered voice + text customer support agent** with RAG (Retrieval-Augmented Generation). The system answers domain-specific questions using a knowledge base, maintains conversation context, detects user sentiment, and supports full voice input/output.

This document covers everything that **must be built and working** before demo day. No shortcuts on anything in this file.

---

## 🏆 Our 4 Core USPs

These are what we pitch. These are what must work flawlessly.

| # | USP | What the judge sees |
|---|---|---|
| 1 | **Voice-first full loop** | Speak → see transcript → response streams in → response is spoken back |
| 2 | **Multi-domain from one system** | One UI, one backend, switch between Banking / E-commerce with a click |
| 3 | **Source-cited answers** | Every response shows which document it came from |
| 4 | **Sentiment-aware responses** | Bot detects frustration and shifts its tone accordingly |

> **Rule:** If any USP is breaking, fix it before adding anything new. A demo with 4 working USPs beats a demo with 8 half-working ones every single time.

---

## 🔌 API & Provider Strategy

### The Provider Pattern (How We Handle Free vs Paid APIs)

Every external service in this project is **swappable via a single `.env` variable.** We never hardcode a provider anywhere. This means:
- Use local/free providers during development and testing
- Swap to premium providers only for final testing or demo day
- No code changes needed, ever. Just change `.env`.

### Environment File (`.env`)
```
# LLM
LLM_PROVIDER=gemini          # options: gemini | groq

# Speech to Text
STT_PROVIDER=local            # options: local | deepgram

# Text to Speech
TTS_PROVIDER=edge             # options: edge | elevenlabs

# API Keys (fill in your own)
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
DEEPGRAM_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
```

---

### Provider Reference Table

| Service | Primary (Free/Always) | Fallback (Credits/Premium) | Notes |
|---|---|---|---|
| **LLM** | Gemini 2.0 Flash | Groq (Llama 3.3 70B) | Both free, Groq is faster |
| **Embeddings** | Gemini text-embedding-004 | — | Free, no fallback needed |
| **STT** | faster-whisper (local) | Deepgram Nova-2 | Local = free always, Deepgram = $200 credit |
| **TTS** | edge-tts (free) | ElevenLabs | edge-tts has no limits at all |
| **Vector DB** | FAISS (local) | — | Free, no infra needed |

### When to Use What
- **Daily development/testing:** `STT_PROVIDER=local`, `LLM_PROVIDER=gemini`, `TTS_PROVIDER=edge`
- **Full integration testing:** `STT_PROVIDER=deepgram`, everything else same
- **Demo day:** `STT_PROVIDER=deepgram`, `TTS_PROVIDER=edge` or elevenlabs for better voice

---

## 🗂️ Project Folder Structure

```
ai-support-agent/
│
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Reads .env, exposes settings object
│   ├── requirements.txt         # Pinned dependencies
│   ├── .env                     # Never commit this to git
│   ├── .env.example             # Commit this (no real keys)
│   │
│   ├── providers/               # THE SWAP LAYER — all providers live here
│   │   ├── __init__.py
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Abstract base class
│   │   │   ├── gemini.py        # Gemini 2.0 Flash implementation
│   │   │   └── groq.py          # Groq implementation
│   │   ├── stt/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── local_whisper.py # faster-whisper (Mac + Windows CPU)
│   │   │   └── deepgram.py      # Deepgram Nova-2
│   │   └── tts/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── edge_tts.py      # Microsoft edge-tts (always free)
│   │       └── elevenlabs.py    # ElevenLabs (credits)
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingestor.py          # Load docs, chunk, embed, save FAISS index
│   │   ├── retriever.py         # Query FAISS, return top-K chunks with metadata
│   │   └── pipeline.py          # Full RAG: query → retrieve → inject → LLM → respond
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── router.py            # Classifies intent, routes to right handler
│   │   ├── memory.py            # Conversation history per session
│   │   └── sentiment.py         # Detects sentiment from user message
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py              # WebSocket /ws/chat/{session_id}
│   │   └── voice.py             # POST /api/voice — accepts audio, returns transcript
│   │
│   └── data/
│       ├── documents/
│       │   ├── banking/         # PDFs, text files for banking domain
│       │   └── ecommerce/       # PDFs, text files for e-commerce domain
│       └── indexes/
│           ├── banking/         # FAISS index files (auto-generated)
│           └── ecommerce/       # FAISS index files (auto-generated)
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx       # Message list with streaming
│   │   │   ├── MessageBubble.jsx    # Single message + source citation card
│   │   │   ├── VoiceInput.jsx       # Mic button + waveform + transcript preview
│   │   │   ├── SentimentBadge.jsx   # 😊 / 😐 / 😤 indicator
│   │   │   ├── DomainSwitcher.jsx   # Banking / E-commerce tab bar
│   │   │   └── StreamingIndicator.jsx # "Thinking..." animation
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js      # WebSocket connection + message handling
│   │   │   └── useVoiceRecorder.js  # MediaRecorder API (browser audio capture)
│   │   └── services/
│   │       └── api.js               # All fetch/WebSocket calls in one place
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## ⚙️ Backend — How Each Piece Works

### 1. Provider Pattern (The Swap Layer)

Every provider has a **base class** that defines the interface. Implementations just fill it in.

**Example — STT Base:**
```python
# providers/stt/base.py
from abc import ABC, abstractmethod

class BaseSTT(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes) -> str:
        """Takes raw audio bytes, returns transcript string."""
        pass
```

**Local Whisper Implementation:**
```python
# providers/stt/local_whisper.py
from faster_whisper import WhisperModel
from .base import BaseSTT

class LocalWhisperSTT(BaseSTT):
    def __init__(self):
        # int8 + cpu works on both Mac and Windows without GPU
        self.model = WhisperModel("medium", device="cpu", compute_type="int8")

    async def transcribe(self, audio_bytes: bytes) -> str:
        # Write bytes to temp file, transcribe, return text
        ...
```

**The Factory (how the app picks a provider):**
```python
# providers/stt/__init__.py
from config import settings

def get_stt_provider():
    if settings.STT_PROVIDER == "deepgram":
        from .deepgram import DeepgramSTT
        return DeepgramSTT()
    else:
        from .local_whisper import LocalWhisperSTT
        return LocalWhisperSTT()
```

Same exact pattern for LLM and TTS. The rest of the app just calls `get_stt_provider().transcribe(audio)` and never thinks about which provider is active.

---

### 2. RAG Pipeline

**Ingestion (run once per domain, not on every request):**
```
Load documents (PDF / TXT)
    → Split into chunks (512 tokens, 50 token overlap)
    → Embed each chunk using Gemini text-embedding-004
    → Store embeddings + metadata in FAISS index
    → Save index to disk at data/indexes/{domain}/
```

**Query (runs on every user message):**
```
User query
    → Embed query using same Gemini embedding model
    → Search FAISS index → top 4 most similar chunks
    → Each chunk carries metadata: {source_file, page_number, chunk_text}
    → Inject chunks into LLM prompt as context
    → LLM generates answer
    → Response includes source references
```

**Important implementation notes:**
- Always save the FAISS index to disk after ingestion (`faiss.write_index()`). If you don't, it resets every time the server restarts.
- Use `pathlib.Path` for all file paths — this is what makes it work on both Mac and Windows without changes.
- Chunk size 512 tokens with 50 overlap is a safe default. Don't over-tune this early.

---

### 3. Conversation Memory

Simple session-based memory. No database needed.

```python
# agent/memory.py
from collections import deque

# In-memory store: session_id → list of messages
sessions = {}

def get_history(session_id: str, max_turns: int = 8) -> list:
    return list(sessions.get(session_id, deque(maxlen=max_turns)))

def add_turn(session_id: str, role: str, content: str):
    if session_id not in sessions:
        sessions[session_id] = deque(maxlen=16)
    sessions[session_id].append({"role": role, "content": content})
```

The last 8 turns are injected into every LLM prompt. This is what gives the bot memory.

---

### 4. Sentiment Detection

One extra LLM call per user message. Lightweight, fast.

```python
# agent/sentiment.py
async def detect_sentiment(user_message: str, llm) -> str:
    prompt = f"""
    Classify the sentiment of this customer message in one word only.
    Choose from: positive, neutral, frustrated, urgent
    Message: "{user_message}"
    Respond with one word only.
    """
    result = await llm.complete(prompt)
    return result.strip().lower()  # returns "positive" | "neutral" | "frustrated" | "urgent"
```

This result is:
1. Sent to the frontend to display the sentiment badge
2. Used to modify the system prompt tone (frustrated → more empathetic language)

---

### 5. API Endpoints

**WebSocket — Main Chat:**
```
WS /ws/chat/{session_id}?domain={banking|ecommerce}

Client sends:  { "message": "What are your return policies?" }
Server sends:  { "type": "token", "content": "Our " }         ← streaming
               { "type": "token", "content": "return " }
               { "type": "token", "content": "policy..." }
               { "type": "sources", "content": [...] }         ← after stream ends
               { "type": "sentiment", "content": "neutral" }   ← after stream ends
               { "type": "done" }
```

**REST — Voice Input:**
```
POST /api/voice
Content-Type: multipart/form-data
Body: audio file (webm/wav blob from browser)

Response: { "transcript": "What are your return policies?" }
```

The frontend calls `/api/voice` to get the transcript, then sends it through the WebSocket like a normal text message. Clean separation.

---

## 🖥️ Frontend — What We're Building

### UI Layout
```
┌─────────────────────────────────────────────────┐
│  [Banking]  [E-commerce]          😐 Neutral     │  ← Domain switcher + Sentiment
├─────────────────────────────────────────────────┤
│                                                 │
│  [Bot]  Hello! How can I help you today?        │
│                                                 │
│         I want to know about refund policy [Me] │
│                                                 │
│  [Bot]  Our refund policy allows returns        │
│         within 30 days of purchase...           │
│         ┌─────────────────────────────┐         │
│         │ 📄 Source: return_policy.pdf│         │  ← Citation card
│         │    Page 4                   │         │
│         └─────────────────────────────┘         │
│                                                 │
├─────────────────────────────────────────────────┤
│  🎙️ [Mic button]  [Text input field]  [Send]    │  ← Input bar
└─────────────────────────────────────────────────┘
```

### Key Frontend Behaviors

**Streaming text:** Characters appear token by token as the LLM generates them. NOT a loading spinner followed by a full response. This is non-negotiable — it's what makes the UI feel alive.

**Voice flow:**
1. User clicks mic button → button turns red, waveform appears
2. Browser records audio via MediaRecorder API
3. User clicks mic again to stop → audio blob sent to `/api/voice`
4. Transcript appears in text input field
5. Auto-submitted through WebSocket
6. Response streams in, then TTS audio plays automatically

**Source citation cards:** Appear below the bot response as small cards showing filename and page. Clicking them could highlight or open the source (nice to have).

**Sentiment badge:** Top right corner. Updates after every user message. Small, not intrusive.

**Domain switcher:** Tab bar at the top. Switching domain clears the chat and connects to the new domain's FAISS index.

---

## 🪟 Cross-Platform (Mac + Windows) Rules

Follow these rules without exception. They prevent 90% of cross-platform bugs.

| Rule | Why |
|---|---|
| Use `pathlib.Path` for ALL file paths, never string concatenation | Windows uses `\`, Mac uses `/` |
| Everyone uses **Python 3.11 or 3.12+** | 3.11 preferred, 3.12/3.13 fine since llama-index removed |
| Everyone uses a **virtual environment** (`venv`) | No global pip installs |
| `requirements.txt` has **unpinned versions** (llama-index removed, no conflict risk) | Installs cleanly on all Python 3.11+ |
| Audio capture happens in the **browser JS**, not Python | Avoids pyaudio/sounddevice platform hell |
| faster-whisper always uses `device="cpu", compute_type="int8"` | GPU acceleration differs per platform |
| `.env` file: **no spaces around `=`**, no quotes unless needed | Windows dotenv parsing is stricter |

### Setup Commands (Everyone Runs These)
```bash
# Clone repo
git clone <repo-url>
cd ai-support-agent/backend

# Create virtual environment
python -m venv venv

# Activate (Mac/Linux)
source venv/bin/activate
# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env file and fill in your keys
cp .env.example .env
```

---

## 📦 Dependencies (`requirements.txt`)

> **Note:** llama-index was removed due to Python 3.12+ incompatibility. RAG is implemented
> directly using `faiss-cpu`, `pypdf`, and `google-generativeai` for embeddings. No functionality lost.

```
# Backend framework
fastapi
uvicorn[standard]
python-multipart
websockets
python-dotenv
pydantic-settings

# RAG — direct libraries, no llama-index wrapper
faiss-cpu
pypdf

# LLM + Embeddings (Gemini SDK handles both)
google-generativeai
groq

# STT
faster-whisper

# TTS
edge-tts

# HTTP
httpx
aiofiles
```

Frontend (`package.json` key deps):
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "tailwindcss": "^3.4.0"
  }
}
```

---

## 🏗️ Build Order (Follow This Exactly)

Do not skip ahead. Each step must work before moving to the next.

```
Step 1: Gemini answers a hardcoded question in a Python script
        → Confirm API key works, streaming works
        DONE WHEN: You see streaming tokens in terminal

Step 2: RAG pipeline works in isolation
        → Ingest a PDF, ask a question, get an answer with sources
        DONE WHEN: Correct answer returned with filename cited

Step 3: FastAPI wraps the RAG pipeline
        → WebSocket endpoint works, streaming works via REST client (Postman/Thunder)
        DONE WHEN: Postman receives streamed tokens

Step 4: React frontend connects to WebSocket
        → Text input → streaming response → renders correctly
        DONE WHEN: Full text chat works in browser

Step 5: Conversation memory added
        → Bot remembers previous turns in the same session
        DONE WHEN: "What about its price?" after a product question gives correct answer

Step 6: Sentiment detection added
        → Badge updates after each user message
        DONE WHEN: Frustrated message → 😤 badge appears

Step 7: Voice input (STT) added
        → Record in browser → transcript appears → submits as text
        DONE WHEN: Spoken question gets correct text answer

Step 8: Voice output (TTS) added
        → Bot response is spoken aloud after streaming completes
        DONE WHEN: Full voice loop works end to end

Step 9: Domain switcher added
        → Two domains ingested, tab switch loads correct index
        DONE WHEN: Banking question only returns banking docs

Step 10: UI polish
        → Clean layout, good fonts, smooth animations, no rough edges
        DONE WHEN: You'd be proud to screen-record this
```

---

## 🎤 Demo Day Script

Practice this exact flow before demo day.

1. Open the app. Show the domain switcher — "Banking" is selected.
2. Type: *"What documents do I need to open a savings account?"* — show streaming response + source card.
3. Follow up: *"What about the minimum balance?"* — show that it remembers context.
4. Switch to E-commerce domain. Show that the chat clears and the knowledge base changed.
5. Now use voice: click mic, say *"What is your return policy?"* — show waveform, transcript, streaming response, TTS plays back.
6. Type an angry message: *"This is ridiculous, I've been waiting 3 weeks for my order"* — show 😤 badge appear, show bot's empathetic response tone.
7. Point out the source citation card on any answer.

**Total demo time: ~3 minutes.** Rehearse until it's smooth. Every hesitation costs points.

---

## ⚠️ Known Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Voice breaks on demo day | Text chat is fully functional fallback. Never demo voice first. |
| Gemini rate limit hit during heavy testing | Switch `LLM_PROVIDER=groq` in `.env`. Same code, instant swap. |
| Deepgram credits running low | Switch `STT_PROVIDER=local` during development. Use Deepgram only for real testing. |
| FAISS index missing on server start | Ingestion script checks for index file on startup and auto-rebuilds if missing. |
| Windows path error on teammate's machine | All paths use `pathlib.Path`. Test on Windows in Week 1, not Week 2. |
| Internet down at venue | Keep `ollama` with `llama3.2:3b` installed on main laptop as emergency LLM. Keep `STT_PROVIDER=local` ready. |