# AI Customer Support Agent

LLM-powered voice + text support agent with RAG, sentiment detection, and multi-domain switching.

---

## First Time Setup (Everyone Does This)

```bash
# 1. Clone and enter repo
git clone <repo-url>
cd ai-support-agent

# 2. Create your branch — use your member number
git checkout -b m2   # change to m1, m2, m3 as appropriate

# 3. Run the structure setup script (once only)
bash setup_structure.sh

# 4. Backend setup
cd backend
python -m venv venv

# Activate — Mac/Linux:
source venv/bin/activate
# Activate — Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# 5. Create your env file
cp .env.example .env
# Open .env and fill in your API keys
```

---

## M3 Note — Your .env Must Have This
```
STT_PROVIDER=deepgram
```
Never use `STT_PROVIDER=local` on your machine. Whisper won't run well on your hardware.

---

## M2 (Frontend) — Running the Mock Server

You don't need the real backend. Run this instead:

```bash
# From repo root
pip install fastapi uvicorn  # one time only
uvicorn mock_server:app --reload --port 8000
```

Then in your frontend `.env` or config:
```
VITE_WS_URL=ws://localhost:8000
VITE_API_URL=http://localhost:8000
```

When M1 shares an ngrok URL, just swap those two values. Nothing else changes.

---

## Running the Real Backend

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn main:app --reload --port 8000
```

## Running Frontend + Backend Together

```bash
# Terminal 1 - backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn main:app --reload --port 8000

# Terminal 2 - frontend
cd frontend
npm install
npm run dev
```

Frontend defaults to `http://localhost:8000`.  
If needed, set `VITE_API_BASE_URL` before running dev server.

---

## Daily Git Workflow

```bash
# Start of every session — always do this first
git pull origin main

# Work on your code

# End of session — always commit before closing
git add .
git commit -m "brief description of what you did"
git push origin yourbranchname   # m1, m2, or m3
```

**Never push directly to main. M1 handles all merges into main.**

---

## Docs

| File | Purpose |
|---|---|
| `docs/CORE.md` | Full architecture, stack, build order |
| `docs/TEAM.md` | Who owns what, timeline |
| `docs/API_CONTRACT.md` | WebSocket and REST endpoint shapes — sacred |
| `docs/EXTRAS.md` | Bonus features after core is done |
| `logs/mx.local.md` | Your personal AI session log — never committed |
