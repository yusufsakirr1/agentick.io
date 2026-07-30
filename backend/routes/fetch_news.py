"""
Haber çekme ve arama endpoint'leri.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.auth import get_current_user
from backend.constants import validate_ticker

from src.ingestion.news_client import (
    fetch_news_if_stale, cleanup_old_news, search_news_for_ticker,
)

router = APIRouter()

MAX_TOP_K = 50


class NewsSearchRequest(BaseModel):
    ticker: str = "THYAO"
    query: str = ""
    top_k: int = Field(default=10, ge=1, le=MAX_TOP_K)


@router.post("/fetch-news")
def fetch_news(current_user: dict = Depends(get_current_user)):
    """RSS kaynaklarından haberleri çeker (cache bayatsa)."""
    new_count = fetch_news_if_stale()
    deleted = cleanup_old_news()
    return {
        "new_articles": new_count,
        "deleted_old": deleted,
    }


@router.post("/news/search")
def search_news_endpoint(req: NewsSearchRequest, current_user: dict = Depends(get_current_user)):
    """Haber arama endpoint'i — sadece BIST-30 ticker'ları."""
    ticker = validate_ticker(req.ticker)
    articles = search_news_for_ticker(ticker, query=req.query, top_k=req.top_k)
    return {
        "ticker": ticker,
        "query": req.query,
        "count": len(articles),
        "articles": articles,
    }
