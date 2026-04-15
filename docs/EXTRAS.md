# ⚡ AI Customer Support Agent — EXTRAS & BONUS FEATURES
### Only touch this after everything in CORE.md is working perfectly.

---

## How to Use This Document

This file contains everything that can take the project from "strong competitor" to "winner." None of these are required. Each item is independent — you can pick any of them without needing the others.

Each feature is rated on two axes:

- **Impact:** How much does this impress judges / improve the product?
- **Effort:** How long will this realistically take to build?

Pick the ones with the best impact-to-effort ratio given your remaining time.

---

## Tier 1 — High Impact, Low Effort
### Do these first if you have extra time. Each takes under a day.

---

### 1. Escalation Detection + Ticket Creation
**Impact: ★★★★★ | Effort: ★★☆☆☆**

If the user's sentiment stays at "frustrated" for 2+ consecutive turns, the agent automatically creates a support ticket and tells the user.

**What the judge sees:** The bot says *"I've escalated this to our support team. Ticket #1042 has been created."* A ticket appears in a visible list in the UI. This is a real agentic behavior — the system made a decision and took an action.

**How to build it:**
- Add a `tickets` list in memory (or write to a JSON file)
- In the chat handler, check if last 2 sentiments were both `frustrated`
- If yes: generate a ticket ID, write the conversation summary, return ticket info in the response
- Show a "Escalated Tickets" panel in the UI (even a simple list works)

**Code sketch:**
```python
# agent/router.py
async def check_escalation(session_id: str, current_sentiment: str):
    history = get_sentiment_history(session_id)
    if len(history) >= 2 and all(s == "frustrated" for s in history[-2:]):
        ticket = create_ticket(session_id)
        return ticket  # {"ticket_id": "1042", "status": "open"}
    return None
```

---

### 2. Query Rewriting
**Impact: ★★★★☆ | Effort: ★★☆☆☆**

Before RAG retrieval, run a lightweight LLM call that rewrites the user's query to be more search-friendly. This dramatically improves retrieval quality for vague or conversational questions.

**What the judge sees:** User asks *"the thing about fees I was asking about earlier"* and the bot still gives a correct answer. Without this, RAG would retrieve irrelevant chunks because it's literally searching for "the thing."

**How to build it:**
```python
# rag/pipeline.py
async def rewrite_query(original_query: str, history: list, llm) -> str:
    prompt = f"""
    Given this conversation history and the user's latest message,
    rewrite the message as a clear, standalone search query.
    
    History: {history[-4:]}
    Latest message: "{original_query}"
    
    Respond with only the rewritten query, nothing else.
    """
    return await llm.complete(prompt)
```

Use the rewritten query for FAISS search, but show the original message in the UI.

---

### 3. Typing Indicator + Agent Status Line
**Impact: ★★★★☆ | Effort: ★☆☆☆☆**

While the backend is processing, show a subtle status message that changes based on what the agent is doing.

**What the judge sees:** Instead of a blank loading spinner, they see:
- *"Searching knowledge base..."* (during FAISS retrieval)
- *"Generating response..."* (during LLM call)

This makes the system feel intelligent and transparent. It's the difference between a loading spinner and a system that communicates what it's thinking.

**How to build it:**
- Before FAISS retrieval, send a WebSocket message: `{ "type": "status", "content": "Searching knowledge base..." }`
- Before LLM call, send: `{ "type": "status", "content": "Generating response..." }`
- Frontend shows this in a subtle italics line above the response

Two extra WebSocket sends. That's it.

---

### 4. Suggested Follow-up Questions
**Impact: ★★★★☆ | Effort: ★★☆☆☆**

After every bot response, show 2-3 clickable suggested questions the user might want to ask next.

**What the judge sees:** After answering a refund policy question, three buttons appear: *"How long does the refund take?"* / *"Can I exchange instead?"* / *"What items are non-refundable?"* — clicking any of them submits it as the next message.

**How to build it:**
- After generating the main response, make one more LLM call:
```python
prompt = f"""
Based on this conversation, suggest 3 short follow-up questions the user might ask.
Return them as a JSON array of strings. Nothing else.
Context: {last_response}
"""
```
- Parse the JSON, send as `{ "type": "suggestions", "content": ["...", "...", "..."] }`
- Frontend renders them as clickable chips below the response

---

### 5. Language Auto-Detection
**Impact: ★★★☆☆ | Effort: ★☆☆☆☆**

Detect what language the user is writing in and respond in the same language. Gemini handles this natively — you don't need a translation pipeline.

**What the judge sees:** User types in Hindi → bot responds in Hindi. User switches to English mid-conversation → bot follows. Multi-language support as a free feature.

**How to build it:**
```python
# Add to system prompt
system_prompt = """
You are a customer support assistant. 
Always respond in the same language the user is writing in.
If they write in Hindi, respond in Hindi.
If they write in English, respond in English.
"""
```

That's literally the entire implementation. One line added to your system prompt. Mention it prominently in your pitch.

---

## Tier 2 — High Impact, Medium Effort
### These are worth doing if you have 2-3 days to spare after Tier 1.

---

### 6. Admin Document Upload Panel
**Impact: ★★★★★ | Effort: ★★★☆☆**

A simple admin page where you can drag-and-drop a new PDF and it gets ingested into the active domain's knowledge base in real time.

**What the judge sees:** You upload a new document during the demo. Then immediately ask a question about it. The bot answers correctly. This proves the RAG pipeline is live and not just pre-loaded static data.

**How to build it:**
- Frontend: drag-and-drop file upload component (react-dropzone, simple to use)
- Backend: `POST /api/admin/ingest` accepts a PDF, runs the ingestion pipeline, rebuilds FAISS index
- Show a progress indicator: *"Ingesting document... Done! 47 chunks indexed."*
- The new knowledge is immediately available in the chat

This is one of the most impressive live demos you can do. Judges can suggest their own document.

---

### 7. Confidence Score on Responses
**Impact: ★★★★☆ | Effort: ★★★☆☆**

Show a confidence indicator on each response based on how similar the retrieved chunks were to the query.

**What the judge sees:** High-confidence answers show a green indicator. Low-confidence answers (where RAG couldn't find a great match) show yellow and include a disclaimer like *"I'm not fully certain about this — please verify."*

**How to build it:**
- FAISS returns similarity scores alongside results
- Average the top-3 similarity scores
- Map score to confidence level: `>0.85 = high`, `0.65–0.85 = medium`, `<0.65 = low`
- Inject into system prompt: *"Confidence in retrieved context: LOW. Acknowledge uncertainty."*
- Show a colored dot in the UI next to each response

This directly addresses the #1 problem with AI systems — blind overconfidence. Judges in enterprise/banking contexts will specifically appreciate this.

---

### 8. Conversation Export
**Impact: ★★★☆☆ | Effort: ★★☆☆☆**

Let the user download their conversation as a PDF or text file.

**What the judge sees:** A "Export Chat" button. Clicking it downloads a clean formatted transcript of the conversation with timestamps, source citations included.

**Why it matters:** It signals that this is a production-ready tool, not just a demo. Real support systems need audit trails.

**How to build it:**
- Backend: `GET /api/sessions/{session_id}/export` — formats conversation history as markdown or plain text
- Frontend: triggers download via blob URL
- Include: timestamp, user messages, bot responses, sources cited, sentiment at each turn

---

### 9. Response Tone Profiles
**Impact: ★★★☆☆ | Effort: ★★☆☆☆**

Let the admin configure the bot's personality. Options like "Formal", "Friendly", "Concise" — each maps to a different system prompt.

**What the judge sees:** A settings toggle. Switch from "Formal" to "Friendly" and the bot's language visibly changes. Same knowledge base, different personality.

**Why it matters:** This shows that the system is configurable for different business contexts. A bank wants formal. An e-commerce startup wants friendly.

**How to build it:**
```python
TONE_PROMPTS = {
    "formal": "Respond in professional, formal language. Be precise and thorough.",
    "friendly": "Respond in a warm, conversational tone. Use simple language.",
    "concise": "Be extremely brief. Answer in 1-3 sentences maximum."
}
# Inject selected tone into system prompt
```
Dropdown in frontend, stored in session state, passed as query param.

---

## Tier 3 — Maximum Impression, Higher Effort
### Only if your core is rock solid and you have 3+ days left. These are the difference between winning and placing.

---

### 10. Analytics Dashboard
**Impact: ★★★★★ | Effort: ★★★★☆**

A live dashboard showing:
- Total conversations today
- Most asked questions (topic clustering)
- Sentiment breakdown across all sessions (% positive / neutral / frustrated)
- Average response time
- Most accessed documents

**What the judge sees:** A real product. Not just a chatbot but a system a business would actually pay for. This is the "business value" component that enterprise-focused judges care about most.

**How to build it:**
- Log every conversation turn to SQLite: `(session_id, timestamp, role, message, sentiment, sources_used, response_time_ms)`
- `GET /api/analytics` aggregates the data
- Frontend: simple charts using Recharts (already works with React, no extra install complexity)
- Auto-refresh every 30 seconds

---

### 11. Streaming Voice Response (Truly Real-Time)
**Impact: ★★★★★ | Effort: ★★★★☆**

Instead of waiting for the full LLM response to be generated before playing TTS audio, stream the text to TTS sentence by sentence. The bot starts speaking while still generating the rest of the answer.

**What the judge sees:** Latency from question to first spoken word drops from ~3 seconds to ~1 second. The conversation feels genuinely real-time, like talking to a person.

**How to build it:**
- Split LLM stream on sentence boundaries (`.`, `?`, `!`)
- As each sentence completes, immediately send it to TTS
- Queue the audio chunks and play them sequentially in the browser
- This requires careful async coordination between streaming text and audio playback

This is technically the hardest thing in this document. Don't attempt it unless everything else is perfect.

---

### 12. Hybrid Search (BM25 + Semantic)
**Impact: ★★★★☆ | Effort: ★★★★☆**

Combine keyword-based search (BM25) with semantic vector search (FAISS). Merge results using Reciprocal Rank Fusion. This significantly improves retrieval on edge cases — especially exact product names, account numbers, or specific terminology that semantic search can miss.

**What the judge sees:** Nothing directly. But answers to specific, precise questions are noticeably more accurate. This is the kind of thing you mention in the architecture explanation.

**How to build it:**
- Install `rank_bm25` library
- Build a BM25 index over the same chunks as FAISS
- On each query, get top-10 from FAISS and top-10 from BM25
- Merge using Reciprocal Rank Fusion formula
- Use merged top-4 as context for LLM

---

## 🗣️ What to Say in the Pitch

Even if you only build Tier 1 extras, here's how to frame the full system to maximize judge impression:

> *"Most support bots are search engines with a chat wrapper. Ours is different in four ways.*
>
> *First, it's voice-native — you can speak to it and hear responses back, end to end.*
>
> *Second, it's source-transparent — every answer cites the exact document it came from, which matters in regulated industries like banking.*
>
> *Third, it's emotionally intelligent — it tracks sentiment across a conversation and escalates to a human agent when a customer is consistently frustrated.*
>
> *Fourth, it's domain-agnostic — the same system works for banking, e-commerce, or healthcare just by changing the knowledge base.*
>
> *The architecture is also provider-agnostic — we can swap any AI component, LLM, STT, or TTS, without changing any business logic. That's important for production systems where you might want to switch providers based on cost or performance."*

That's a 60-second pitch that covers architecture, innovation, and business value. Practice it.

---

## Priority Order (If Time Is Running Out)

```
Must have (CORE.md):        USPs 1-4, voice loop, domain switcher, citations, sentiment
Do next (Tier 1):           Escalation tickets, query rewriting, status line, suggestions
Then (Tier 2):              Admin upload panel, confidence scores
Only if ahead (Tier 3):     Analytics dashboard, streaming voice, hybrid search
```

**The goal is a demo where everything you show works perfectly.** A project with 6 polished features beats a project with 12 half-broken ones. Every time.
