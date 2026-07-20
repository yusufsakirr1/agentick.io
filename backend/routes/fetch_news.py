"""
Haber çekme ve arama endpoint'leri.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from src.ingestion.news_client import fetch_news_if_stale, cleanup_old_news, search_news

router = APIRouter()


class NewsSearchRequest(BaseModel):
    ticker: str = "THYAO"
    query: str = ""
    top_k: int = 10


@router.post("/fetch-news")
def fetch_news():
    """RSS kaynaklarından haberleri çeker (cache bayatsa)."""
    new_count = fetch_news_if_stale()
    deleted = cleanup_old_news()
    return {
        "new_articles": new_count,
        "deleted_old": deleted,
    }


@router.post("/news/search")
def search_news_endpoint(req: NewsSearchRequest):
    """Haber arama endpoint'i."""
    articles = search_news(ticker=req.ticker, query=req.query, top_k=req.top_k)
    return {
        "ticker": req.ticker,
        "query": req.query,
        "count": len(articles),
        "articles": articles,
    }
