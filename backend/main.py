"""SupportLens — FastAPI application entrypoint."""

from dotenv import load_dotenv

load_dotenv()  # Load .env before any other imports read os.environ

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from routes import router

app = FastAPI(title="SupportLens")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def startup():
    init_db()
