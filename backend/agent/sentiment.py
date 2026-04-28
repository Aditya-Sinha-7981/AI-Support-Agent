from __future__ import annotations

import asyncio
import json
import re

ALLOWED_SENTIMENTS = {"positive", "neutral", "frustrated"}

NEGATIVE_PHRASES = [
    "not working",
    "still not",
    "doesn't work",
    "wont work",
    "won't work",
    "can't login",
    "cannot login",
    "fed up",
    "waste of time",
    "worst",
    "broken",
    "issue",
    "problem",
    "error",
    "failed",
    "failure",
    "frustrating",
    "annoying",
    "ridiculous",
    "unacceptable",
    "terrible",
    "useless",
    "horrible",
    "pathetic",
    "angry",
    "furious",
    "upset",
    "disappointed",
    "disgusted",
    "hate this",
    "so bad",
    "very bad",
    "keep failing",
    "not resolved",
    "still broken",
    "keeps happening",
    "not good",
    "so hard",
]

POSITIVE_PHRASES = [
    "thank you",
    "thanks",
    "worked",
    "resolved",
    "fixed",
    "great",
    "awesome",
    "perfect",
    "love it",
    "helpful",
    "excellent",
    "amazing",
    "appreciate",
    "fantastic",
    "good job",
    "well done",
    "happy",
    "satisfied",
    "impressed",
    "wonderful",
    "brilliant",
    "superb",
]

INTENSIFIERS = ["very", "really", "so", "extremely", "totally", "absolutely", "completely"]
SOFTENERS = ["maybe", "kinda", "slightly", "a bit", "somewhat", "sort of", "kind of"]
NEGATIONS = [
    "not",
    "never",
    "no",
    "cant",
    "can't",
    "won't",
    "wont",
    "doesn't",
    "dont",
    "don't",
    "isn't",
    "isnt",
]

_WORD_RE = re.compile(r"[a-z']+")

_POSITIVE_WORDS = {
    "thank",
    "thanks",
    "worked",
    "work",
    "working",
    "resolved",
    "resolve",
    "fixed",
    "fix",
    "great",
    "awesome",
    "perfect",
    "helpful",
    "excellent",
    "amazing",
    "appreciate",
    "fantastic",
    "happy",
    "satisfied",
    "impressed",
    "wonderful",
    "brilliant",
    "superb",
    "good",
    "love",
}

_NEGATIVE_WORDS = {
    "bad",
    "hard",
    "worst",
    "broken",
    "issue",
    "problem",
    "error",
    "failed",
    "failure",
    "frustrating",
    "frustrated",
    "annoying",
    "ridiculous",
    "unacceptable",
    "terrible",
    "useless",
    "horrible",
    "pathetic",
    "angry",
    "furious",
    "upset",
    "disappointed",
    "disgusted",
    "hate",
    "failing",
}


def _normalize(text: str) -> str:
    lowered = (text or "").lower().strip()
    lowered = re.sub(r"\s+", " ", lowered)
    lowered = re.sub(r"[^a-z0-9\s!?']", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip()


def _tokenize_words(normalized_text: str) -> list[str]:
    return _WORD_RE.findall(normalized_text)


def _phrase_occurrences(tokens: list[str], phrase: str) -> int:
    phrase_tokens = _tokenize_words(phrase)
    if not phrase_tokens or len(tokens) < len(phrase_tokens):
        return 0
    width = len(phrase_tokens)
    hits = 0
    for i in range(len(tokens) - width + 1):
        if tokens[i : i + width] == phrase_tokens:
            hits += 1
    return hits


def _local_score(text: str) -> tuple[str, bool]:
    normalized_text = _normalize(text)
    tokens = _tokenize_words(normalized_text)
    if not tokens:
        return "neutral", False

    pos = 0
    neg = 0

    # 1) phrase scan first
    for phrase in NEGATIVE_PHRASES:
        neg += 2 * _phrase_occurrences(tokens, phrase)
    for phrase in POSITIVE_PHRASES:
        pos += 2 * _phrase_occurrences(tokens, phrase)

    # 2) token-level scoring
    token_count = len(tokens)
    for i, token in enumerate(tokens):
        if token in _POSITIVE_WORDS:
            back_window = tokens[max(0, i - 2) : i]
            if any(t in NEGATIONS for t in back_window):
                neg += 1
            else:
                pos += 1
        if token in _NEGATIVE_WORDS:
            neg += 1

        if token in NEGATIONS:
            lookahead = tokens[i + 1 : min(token_count, i + 3)]
            if any(t in _POSITIVE_WORDS for t in lookahead):
                pos = max(0, pos - 2)
                neg += 1
            if any(t in _NEGATIVE_WORDS for t in lookahead):
                neg = max(0, neg - 1)

        if token in INTENSIFIERS and i + 1 < token_count:
            nxt = tokens[i + 1]
            if nxt in _NEGATIVE_WORDS:
                neg += 1
            if nxt in _POSITIVE_WORDS:
                pos += 1

        if token in SOFTENERS:
            neg = max(0, neg - 1)
            pos = max(0, pos - 1)

    # 3) intensity signals
    if "!!" in text and neg > 0:
        neg += 1
    if neg > 0:
        raw_tokens = re.findall(r"\b[\w']+\b", text or "")
        if any(tok.isalpha() and len(tok) >= 3 and tok.isupper() for tok in raw_tokens):
            neg += 1

    # 4) classify
    if neg >= 3 and (neg - pos) >= 2:
        label = "frustrated"
    elif pos >= 3 and (pos - neg) >= 2:
        label = "positive"
    else:
        label = "neutral"

    total_signal = pos + neg
    is_uncertain = (
        (total_signal == 0 and len(tokens) > 5)
        or (abs(pos - neg) <= 1 and total_signal > 0)
        or (pos > 0 and neg > 0 and pos >= 2 and neg >= 2)
    )
    return label, is_uncertain


async def _llm_classify_sentiment(message: str, llm) -> str | None:
    prompt = (
        "You are a sentiment classifier for a customer support system.\n"
        "Classify the following customer message into exactly one of: positive, neutral, frustrated\n\n"
        "Rules:\n"
        "- frustrated = complaint, anger, repeated problem, urgency, anything negative\n"
        "- positive = thanks, satisfaction, relief, compliment\n"
        "- neutral = question, request, no emotional signal\n\n"
        'Respond with ONLY valid JSON. Example: {"sentiment": "frustrated"}\n'
        "Do not add explanation, markdown, or any other text.\n\n"
        f'Customer message: "{(message or "")[:500]}"'
    )
    try:
        raw = await asyncio.wait_for(llm.complete(prompt), timeout=3.0)
        payload = json.loads((raw or "").strip())
        if isinstance(payload, dict):
            sentiment = str(payload.get("sentiment", "")).strip().lower()
            if sentiment in ALLOWED_SENTIMENTS:
                return sentiment
    except Exception:
        return None
    return None


async def detect_sentiment(message: str, llm=None) -> str:
    try:
        if not message or not message.strip():
            return "neutral"

        normalized = _normalize(message)
        label, is_uncertain = _local_score(normalized)

        if is_uncertain and llm is not None:
            llm_result = await _llm_classify_sentiment(message, llm)
            if llm_result in ALLOWED_SENTIMENTS:
                return llm_result

        if label in ALLOWED_SENTIMENTS:
            return label
        return "neutral"
    except Exception:
        return "neutral"