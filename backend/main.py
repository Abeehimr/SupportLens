"""SupportLens — FastAPI application entrypoint."""

import logging
import time
import uuid

from dotenv import load_dotenv

load_dotenv()  # Load .env before any other imports read os.environ

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from logging_config import setup_logging
from routes import router

setup_logging()
logger = logging.getLogger(__name__)

START_TIME = time.time()

app = FastAPI(title="SupportLens")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every HTTP request as structured JSON (skip /health)."""
    if request.url.path == "/health":
        return await call_next(request)

    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.time()

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as exc:
        status_code = 500
        logger.error(
            "Unhandled exception",
            extra={
                "event": "unhandled_exception",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        raise

    duration_ms = round((time.time() - start) * 1000)

    logger.info(
        "%s %s %s %dms",
        request.method,
        request.url.path,
        status_code,
        duration_ms,
        extra={
            "event": "http_request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": duration_ms,
        },
    )

    return response


@app.on_event("startup")
def startup():
    init_db()
    logger.info("SupportLens backend started")
