from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel
import time, os
from groq import Groq
from typing import Optional

# --- Groq Setup ---
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
CHAT_SYSTEM_PROMPT = "You are a helpful customer support agent for a SaaS billing platform. Keep responses short and clear."
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


def classify(user_message: str, bot_response: str) -> str:
    resp = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": CLASSIFY_PROMPT},
            {"role": "user", "content": f"User: {user_message}\nBot: {bot_response}"},
        ],
        max_tokens=20,
    )
    raw = resp.choices[0].message.content.strip()
    return raw if raw in CATEGORIES else "General Inquiry"


# --- DB Setup ---
DATABASE_URL = "sqlite:///./supportlens.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

CATEGORIES = ["Billing", "Refund", "Account Access", "Cancellation", "General Inquiry"]


class Trace(Base):
    __tablename__ = "traces"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_message = Column(String, nullable=False)
    bot_response = Column(String, nullable=False)
    category = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    response_time_ms = Column(Integer, nullable=False)


class ChatRequest(BaseModel):
    message: str


# --- App ---
app = FastAPI(title="SupportLens")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest):
    start = time.time()
    # LLM response via Groq
    completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": req.message},
        ],
        max_tokens=256,
    )
    bot_response = completion.choices[0].message.content.strip()
    elapsed = int((time.time() - start) * 1000)
    # Classify via Groq
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


@app.get("/traces")
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


@app.get("/analytics")
def analytics():
    db = SessionLocal()
    traces = db.query(Trace).all()
    db.close()
    total = len(traces)
    if total == 0:
        return {"total": 0, "avg_response_time_ms": 0, "categories": {c: {"count": 0, "percentage": 0} for c in CATEGORIES}}
    avg_ms = round(sum(t.response_time_ms for t in traces) / total)
    counts = {c: 0 for c in CATEGORIES}
    for t in traces:
        if t.category in counts:
            counts[t.category] += 1
    categories = {
        c: {"count": counts[c], "percentage": round(counts[c] / total * 100, 1)}
        for c in CATEGORIES
    }
    return {"total": total, "avg_response_time_ms": avg_ms, "categories": categories}
