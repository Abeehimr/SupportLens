"""LLM interactions via Groq — chat response & classification."""

import logging
import os

from db import CATEGORIES

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
MODEL = "llama-3.1-8b-instant"

# Lazy-initialise the Groq client so the app can start without the key.
_groq_client = None


def _get_client():
    """Return the Groq client, creating it on first call if possible."""
    global _groq_client
    if _groq_client is not None:
        return _groq_client
    if not GROQ_API_KEY:
        return None
    from groq import Groq
    _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


CHAT_SYSTEM_PROMPT = (
    "You are a helpful customer support agent for a SaaS billing platform. "
    "Keep responses short and clear."
)

CLASSIFY_PROMPT = """You are a strict classifier.
Classify the interaction into exactly ONE category:
- Billing
- Refund
- Account Access
- Cancellation
- General Inquiry

Rules:
- Refund overrides Billing.
- Cancellation overrides Billing.
- If multiple intents, choose PRIMARY intent.
- Output ONLY one exact category string.
- No explanation."""

FALLBACK_RESPONSE = (
    "I'm sorry, our AI assistant is currently unavailable. "
    "A support agent will follow up with you shortly."
)


def get_chat_response(user_message: str) -> str:
    """Return a chat completion for the given user message."""
    client = _get_client()
    if client is None:
        logger.warning("GROQ_API_KEY not configured — returning fallback response")
        return FALLBACK_RESPONSE
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=256,
        )
        return completion.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("LLM chat request failed: %s", exc, exc_info=True)
        return FALLBACK_RESPONSE


def classify(user_message: str, bot_response: str) -> str:
    """Classify a user+bot interaction into one of the predefined categories."""
    client = _get_client()
    if client is None:
        logger.warning("GROQ_API_KEY not configured — category set to LLM_UNAVAILABLE")
        return "LLM_UNAVAILABLE"
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": CLASSIFY_PROMPT},
                {"role": "user", "content": f"User: {user_message}\nBot: {bot_response}"},
            ],
            max_tokens=20,
        )
        raw = resp.choices[0].message.content.strip()
        if raw not in CATEGORIES:
            logger.warning("LLM returned unexpected category %r — falling back to General Inquiry", raw)
            return "General Inquiry"
        return raw
    except Exception as exc:
        logger.error("LLM classify request failed: %s", exc, exc_info=True)
        return "LLM_UNAVAILABLE"
