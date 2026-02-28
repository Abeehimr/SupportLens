"""Database setup, models, and session factory."""

import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/supportlens",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

CATEGORIES = [
    "Billing",
    "Refund",
    "Account Access",
    "Cancellation",
    "General Inquiry",
]


class Trace(Base):
    __tablename__ = "traces"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_message = Column(String, nullable=False)
    bot_response = Column(String, nullable=False)
    category = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    response_time_ms = Column(Integer, nullable=False)


@contextmanager
def get_db():
    """Yield a SQLAlchemy session and guarantee it is closed afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
