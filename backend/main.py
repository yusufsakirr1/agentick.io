"""
Agentick FastAPI uygulaması.

Başlatmak için:
    uv run uvicorn backend.main:app --reload --port 8000
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# Uygulama genelinde logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

from backend.auth import init_auth, is_dev_mode
from backend.routes.upload import router as upload_router
from backend.routes.query import router as query_router
from backend.routes.fetch_data import router as fetch_router
from backend.routes.fetch_news import router as news_router
from backend.routes.compare import router as compare_router
from backend.routes.portfolio import router as portfolio_router

VERSION = "0.4.0"

DEFAULT_DEV_ORIGINS = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]


def _cors_origins() -> list[str]:
    """
    İzinli origin'leri CORS_ORIGINS ortam değişkeninden okur (virgülle ayrılmış).
    Tanımlı değilse yerel geliştirme adresleri kullanılır.
    """
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        return DEFAULT_DEV_ORIGINS
    origins = [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]
    if "*" in origins:
        # allow_credentials=True ile "*" tarayıcı tarafından reddedilir ve
        # kimlik bilgisi taşıyan istekleri sessizce bozar.
        logger.error("CORS_ORIGINS='*' desteklenmiyor (allow_credentials aktif). Yerel varsayılana dönülüyor.")
        return DEFAULT_DEV_ORIGINS
    return origins


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Yanlış yapılandırmada servis hiç ayağa kalkmasın (istek anında 500 yerine)
    init_auth()
    if is_dev_mode():
        logger.warning("Auth DEV MODE aktif — kimlik doğrulama bypass ediliyor.")
    logger.info("CORS izinli origin'ler: %s", ", ".join(_cors_origins()))
    yield


app = FastAPI(
    title="Agentick API",
    description="BIST hisse senedi finansal analiz platformu — Agentic RAG",
    version=VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api", tags=["upload"])
app.include_router(query_router, prefix="/api", tags=["query"])
app.include_router(fetch_router, prefix="/api", tags=["fetch"])
app.include_router(news_router, prefix="/api", tags=["news"])
app.include_router(compare_router, prefix="/api", tags=["compare"])
app.include_router(portfolio_router, prefix="/api", tags=["portfolio"])


@app.get("/api/health")
def health():
    return {"status": "ok", "version": VERSION}
