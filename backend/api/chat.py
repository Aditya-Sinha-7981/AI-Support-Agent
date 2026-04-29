import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import time

from agent.escalation import maybe_create_ticket
from agent.memory import add_turn, clear, get_history
from agent.router import route
from rag.pipeline import pipeline

router = APIRouter()
logger = logging.getLogger("ai_support.chat")

VALID_DOMAINS = {"banking", "ecommerce"}
VALID_TONES = {"neutral", "formal", "friendly", "concise"}
_session_domains: dict[str, str] = {}


async def _send_turn_end(
    websocket: WebSocket,
    *,
    sources: list | None = None,
    confidence: dict | None = None,
    sentiment: str = "neutral",
    suggestions: list[str] | None = None,
    ticket: dict | None = None,
) -> None:
    await websocket.send_json({"type": "sources", "content": sources or []})
    await websocket.send_json({"type": "confidence", "content": confidence or {"score": 0.0, "level": "low"}})
    await websocket.send_json({"type": "sentiment", "content": sentiment})
    if suggestions:
        await websocket.send_json({"type": "suggestions", "content": suggestions})
    if ticket:
        await websocket.send_json({"type": "ticket", "content": ticket})
    await websocket.send_json({"type": "done"})


@router.websocket("/ws/chat/{session_id}")
async def chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info("WS connected session=%s", session_id)

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "").strip()
            logger.info(
                "WS recv session=%s chars=%d text=%r",
                session_id,
                len(message),
                message[:180],
            )
            if not message:
                await websocket.send_json(
                    {"type": "token", "content": "Please send a non-empty message."}
                )
                await _send_turn_end(websocket)
                continue

            # 1. Domain handling
            domain = websocket.query_params.get("domain", "banking")
            if domain not in VALID_DOMAINS:
                domain = "banking"
            logger.info("WS domain session=%s domain=%s", session_id, domain)
            last_domain = _session_domains.get(session_id)
            if last_domain and last_domain != domain:
                clear(session_id)
            _session_domains[session_id] = domain

            target = route(message)
            logger.info("WS route session=%s target=%s", session_id, target)
            if target == "empty":
                await websocket.send_json(
                    {"type": "token", "content": "Please send a non-empty message."}
                )
                await _send_turn_end(websocket)
                continue
            if target == "handoff":
                response = (
                    "I can help with policy and support questions here. "
                    "If you need a human agent, please share your issue details and I will guide next steps."
                )
                await websocket.send_json({"type": "token", "content": response})
                add_turn(session_id, "user", message)
                add_turn(session_id, "assistant", response)
                await _send_turn_end(websocket, sentiment="neutral")
                continue

            # 2. Memory (before pipeline)
            history = get_history(session_id)
            add_turn(session_id, "user", message, meta={"ts": time.time()})

            # 3. Pipeline call
            tone = websocket.query_params.get("tone", "neutral").strip().lower()
            if tone not in VALID_TONES:
                tone = "neutral"
            full_response = ""
            token_count = 0
            ticket: dict | None = None
            try:
                await websocket.send_json(
                    {"type": "status", "content": "Searching knowledge base..."}
                )
                sent_generating_status = False
                async for token in pipeline.query(message, domain, history, tone=tone):
                    if not sent_generating_status:
                        await websocket.send_json(
                            {"type": "status", "content": "Generating response..."}
                        )
                        sent_generating_status = True
                    full_response += token
                    token_count += 1

                    await websocket.send_json({
                        "type": "token",
                        "content": token
                    })

                ticket = maybe_create_ticket(
                    session_id,
                    sentiment=pipeline.last_sentiment,
                    user_message=message,
                    assistant_reply=full_response,
                )
                if ticket:
                    escalation_note = (
                        "\n\nI have escalated this to our support team. "
                        f"Ticket #{ticket['ticket_id']} has been created."
                    )
                    await websocket.send_json({"type": "token", "content": escalation_note})
                    full_response += escalation_note

                # 4. Sources → sentiment → done (API contract order)
                await _send_turn_end(
                    websocket,
                    sources=pipeline.last_sources,
                    confidence=pipeline.last_confidence,
                    sentiment=pipeline.last_sentiment,
                    suggestions=pipeline.last_suggestions,
                    ticket=ticket,
                )
                logger.info(
                    "WS done session=%s tokens=%d resp_chars=%d sentiment=%s sources=%s preview=%r",
                    session_id,
                    token_count,
                    len(full_response),
                    pipeline.last_sentiment,
                    pipeline.last_sources,
                    full_response[:220],
                )
            except Exception as exc:  # noqa: BLE001
                err = str(exc).lower()
                if "quota" in err or "429" in err:
                    fallback = (
                        "I am temporarily rate-limited right now. "
                        "Please try again in a moment."
                    )
                elif "unavailable" in err or "503" in err or "high demand" in err:
                    fallback = (
                        "The AI model is under high demand right now. "
                        "Please retry in a few seconds."
                    )
                else:
                    fallback = (
                        "I could not process that request right now. "
                        "Please verify backend setup and try again."
                    )
                full_response = fallback
                logger.exception("WS pipeline failure session=%s", session_id)
                await websocket.send_json({"type": "token", "content": fallback})
                await _send_turn_end(websocket)

            add_turn(
                session_id,
                "assistant",
                full_response,
                meta={
                    "ts": time.time(),
                    "sentiment": pipeline.last_sentiment,
                    "sources": pipeline.last_sources,
                    "confidence": pipeline.last_confidence,
                    "suggestions": pipeline.last_suggestions,
                    "ticket": ticket,
                },
            )

    except WebSocketDisconnect:
        _session_domains.pop(session_id, None)
        logger.info("WS disconnected session=%s", session_id)
