"""FastAPI route handlers."""

import time
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from db import CATEGORIES, SessionLocal, Trace
from llm import classify, get_chat_response

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/chat")
def chat(req: ChatRequest):
    start = time.time()

    bot_response = get_chat_response(req.message)
    elapsed = int((time.time() - start) * 1000)

    category = classify(req.message, bot_response)

    db = SessionLocal()
    trace = Trace(
        user_message=req.message,
        bot_response=bot_response,
        category=category,
        response_time_ms=elapsed,
    )
    db.add(trace)
    db.commit()
    db.refresh(trace)
    db.close()

    return {
        "id": trace.id,
        "bot_response": trace.bot_response,
        "category": trace.category,
        "response_time_ms": trace.response_time_ms,
    }


@router.get("/traces")
def get_traces(category: Optional[str] = None):
    db = SessionLocal()
    q = db.query(Trace).order_by(Trace.timestamp.desc())
    if category and category in CATEGORIES:
        q = q.filter(Trace.category == category)
    traces = q.all()
    db.close()
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
    db = SessionLocal()
    traces = db.query(Trace).all()
    db.close()

    total = len(traces)
    if total == 0:
        return {
            "total": 0,
            "avg_response_time_ms": 0,
            "categories": {
                c: {"count": 0, "percentage": 0} for c in CATEGORIES
            },
        }

    avg_ms = round(sum(t.response_time_ms for t in traces) / total)
    counts = {c: 0 for c in CATEGORIES}
    for t in traces:
        if t.category in counts:
            counts[t.category] += 1

    categories = {
        c: {
            "count": counts[c],
            "percentage": round(counts[c] / total * 100, 1),
        }
        for c in CATEGORIES
    }
    return {
        "total": total,
        "avg_response_time_ms": avg_ms,
        "categories": categories,
    }
