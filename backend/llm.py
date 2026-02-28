"""LLM interactions via Groq — chat response & classification."""

import os

from groq import Groq

from db import CATEGORIES

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

MODEL = "llama-3.1-8b-instant"

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


def get_chat_response(user_message: str) -> str:
    """Return a chat completion for the given user message."""
    completion = groq_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=256,
    )
    return completion.choices[0].message.content.strip()


def classify(user_message: str, bot_response: str) -> str:
    """Classify a user+bot interaction into one of the predefined categories."""
    resp = groq_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": CLASSIFY_PROMPT},
            {"role": "user", "content": f"User: {user_message}\nBot: {bot_response}"},
        ],
        max_tokens=20,
    )
    raw = resp.choices[0].message.content.strip()
    return raw if raw in CATEGORIES else "General Inquiry"
