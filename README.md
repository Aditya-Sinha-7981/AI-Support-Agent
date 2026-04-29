# AI Customer Support Agent

LLM-powered voice + text support agent with RAG, sentiment detection, source citations, escalation, and multi-domain chat.

## What Is Implemented

### Backend
- FastAPI app with CORS and health endpoints.
- WebSocket chat endpoint with token streaming:
  - `WS /ws/chat/{session_id}?domain={banking|ecommerce}&tone={neutral|formal|friendly|concise}`
  - Streams `status` and `token` messages.
  - Sends `sources`, `confidence`, `sentiment`, optional `suggestions`, optional `ticket`, then `done`.
- RAG pipeline in `backend/rag/pipeline.py`:
  - Domain-aware retrieval (`banking`, `ecommerce`) using FAISS.
  - Confidence scoring from retrieval scores.
  - Conversation-aware query rewriting for short referential follow-ups.
  - Tone-controlled responses.
  - Sentiment detection (`positive`, `neutral`, `frustrated`).
  - Follow-up suggestion generation.
  - Response caching and Groq fallback on Gemini quota errors (if configured).
- Voice/STT endpoint:
  - `POST /api/voice` accepts `webm/wav` and returns transcript JSON.
- TTS endpoint:
  - `POST /api/tts` returns `audio/mpeg`.
- Admin ingestion endpoint:
  - `POST /api/admin/ingest` uploads `.pdf/.txt/.md`, ingests to index, refreshes retriever state.
- Conversation export endpoint:
  - `GET /api/sessions/{session_id}/export` returns downloadable text audit trail.

### Frontend
- React + Vite UI with:
  - Domain switching (`banking`, `ecommerce`).
  - Per-domain multi-thread chat sessions.
  - Streaming assistant rendering.
  - Suggestions and ticket display.
  - Voice input integration.
  - Auto TTS playback for completed assistant replies.
  - Sentiment indicator and connection state display.
  - Theme toggle and localStorage persistence for theme/chat cache.

### Mock Server
- `mock_server.py` provides backend-compatible WebSocket and voice API shapes for frontend development.

## Project Structure

```text
AI-Support-Agent/
  backend/
    main.py
    config.py
    requirements.txt
    .env.example
    api/
    agent/
    providers/
    rag/
    scripts/
    data/
  frontend/
    src/
    package.json
    vite.config.js
  docs/
    API_CONTRACT.md
    CORE.md
    TEAM.md
    EXTRAS.md
    PROJECT_CONTEXT.md
  mock_server.py
```

## Setup

### 1) Backend

```bash
cd backend
python -m venv venv
```

Activate venv:
- Windows (PowerShell): `venv\Scripts\Activate.ps1`
- Windows (cmd): `venv\Scripts\activate.bat`
- Mac/Linux: `source venv/bin/activate`

Install dependencies:

```bash
pip install -r requirements.txt
```

Create env file:

```bash
cp .env.example .env
```

Then fill required keys in `.env` (at least `GEMINI_API_KEY`; optionally `GROQ_API_KEY`, `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`).

### 2) Frontend

```bash
cd frontend
npm install
```

Optional frontend env:
- `VITE_API_BASE_URL=http://localhost:8000`

If unset, frontend uses same-origin fallback.

## Run

### Real backend + frontend

Terminal 1:

```bash
cd backend
# activate venv
uvicorn main:app --reload --port 8000
```

Terminal 2:

```bash
cd frontend
npm run dev
```

### Frontend with mock backend

From repo root:

```bash
uvicorn mock_server:app --reload --port 8000
```

## Data Ingestion

Before asking domain questions, ingest docs for each domain:

```bash
cd backend
# activate venv
python scripts/ingest_domain.py banking
python scripts/ingest_domain.py ecommerce
```

Domain documents live in:
- `backend/data/documents/banking`
- `backend/data/documents/ecommerce`

Indexes are written under `backend/data/indexes/`.

## API Quick Reference

- `GET /` - backend status message
- `GET /health` - health check
- `WS /ws/chat/{session_id}` - main streaming chat
- `POST /api/voice` - speech-to-text
- `POST /api/tts` - text-to-speech
- `POST /api/admin/ingest` - admin document upload + ingest
- `GET /api/sessions/{session_id}/export` - export chat transcript

## Test/Utility Scripts

`backend/scripts/` includes:
- `test_gemini_stream.py`
- `test_rag_pipeline.py`
- `test_step3_ws.py`
- `test_stt_file.py`
- `test_stt_voice_endpoint.py`
- `test_tts_endpoint.py`
- `test_sentiment_detector.py`

## Documentation

- `docs/API_CONTRACT.md` - WebSocket/REST shapes and ordering rules
- `docs/CORE.md` - architecture and implementation baseline
- `docs/PROJECT_CONTEXT.md` - project context
- `docs/TEAM.md` - team ownership/timeline notes
- `docs/EXTRAS.md` - additional ideas/features
