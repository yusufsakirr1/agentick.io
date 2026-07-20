"""
Agentick FastAPI uygulaması.

Başlatmak için:
    uv run uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.routes.upload import router as upload_router
from backend.routes.query import router as query_router
from backend.routes.fetch_data import router as fetch_router
from backend.routes.fetch_news import router as news_router

app = FastAPI(
    title="Agentick API",
    description="BIST hisse senedi finansal analiz platformu — Agentic RAG",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api", tags=["upload"])
app.include_router(query_router, prefix="/api", tags=["query"])
app.include_router(fetch_router, prefix="/api", tags=["fetch"])
app.include_router(news_router, prefix="/api", tags=["news"])


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.3.0"}
