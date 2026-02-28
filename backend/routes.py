"""FastAPI route handlers."""

import logging
import time
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from db import CATEGORIES, Trace, get_db
from llm import GROQ_API_KEY, classify, get_chat_response

ALL_DISPLAY_CATEGORIES = CATEGORIES + ["LLM_UNAVAILABLE"]

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/health")
def health():
    from main import START_TIME

    uptime_seconds = round(time.time() - START_TIME)

    # ── Database probe ───────────────────────────────────────────────────
    try:
        with get_db() as db:
            db.execute(text("SELECT 1"))
        db_status = "up"
    except Exception as exc:
        logger.error("Health check: database unreachable — %s", exc)
        db_status = "down"

    # ── LLM key check ────────────────────────────────────────────────────
    # If the key is present we assume the provider is reachable.
    # A missing key is "not_configured" — the app still works (fallback
    # responses), so this is degraded, not unhealthy.
    llm_status = "configured" if GROQ_API_KEY else "not_configured"

    # ── Overall status ───────────────────────────────────────────────────
    if db_status == "down":
        status = "unhealthy"
    elif llm_status == "not_configured":
        status = "degraded"
    else:
        status = "healthy"

    return {
        "status": status,
        "uptime_seconds": uptime_seconds,
        "database": {"status": db_status},
        "llm": {"status": llm_status},
    }


@router.post("/chat")
def chat(req: ChatRequest):
    start = time.time()

    bot_response = get_chat_response(req.message)
    elapsed = int((time.time() - start) * 1000)

    category = classify(req.message, bot_response)

    with get_db() as db:
        trace = Trace(
            user_message=req.message,
            bot_response=bot_response,
            category=category,
            response_time_ms=elapsed,
        )
        db.add(trace)
        db.commit()
        db.refresh(trace)

    return {
        "id": trace.id,
        "bot_response": trace.bot_response,
        "category": trace.category,
        "response_time_ms": trace.response_time_ms,
    }


@router.get("/traces")
def get_traces(category: Optional[str] = None):
    with get_db() as db:
        q = db.query(Trace).order_by(Trace.timestamp.desc())
        if category and category in ALL_DISPLAY_CATEGORIES:
            q = q.filter(Trace.category == category)
        traces = q.all()

    return [
        {
            "id": t.id,
            "user_message": t.user_message,
            "bot_response": t.bot_response,
            "category": t.category,
            "timestamp": t.timestamp.isoformat(),
            "response_time_ms": t.response_time_ms,
        }
        for t in traces
    ]


@router.get("/analytics")
def analytics():
    with get_db() as db:
        traces = db.query(Trace).all()

    total = len(traces)
    if total == 0:
        return {
            "total": 0,
            "avg_response_time_ms": 0,
            "categories": {
                c: {"count": 0, "percentage": 0} for c in ALL_DISPLAY_CATEGORIES
            },
        }

    avg_ms = round(sum(t.response_time_ms for t in traces) / total)
    counts = {c: 0 for c in ALL_DISPLAY_CATEGORIES}
    for t in traces:
        if t.category in counts:
            counts[t.category] += 1

    categories = {
        c: {
            "count": counts[c],
            "percentage": round(counts[c] / total * 100, 1),
        }
        for c in ALL_DISPLAY_CATEGORIES
    }
    return {
        "total": total,
        "avg_response_time_ms": avg_ms,
        "categories": categories,
    }
