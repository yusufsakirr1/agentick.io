"""
Karşılaştırma endpoint'leri:
  GET  /api/compare/metrics  — 2-5 ticker için metrik karşılaştırması (LLM gerektirmez)
  POST /api/compare/ask      — Karşılaştırma chat sorusu (multi-ticker agent)
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.auth import get_current_user
from backend.services.metrics_utils import get_conn, build_ticker_metrics, DB_PATH

from src.agent.graph import run_agent

logger = logging.getLogger(__name__)

router = APIRouter()

FETCH_TIMEOUT = 60   # saniye — yfinance veri çekme
AGENT_TIMEOUT = 120  # saniye — LLM agent


@router.get("/compare/metrics")
async def compare_metrics(tickers: str = Query(..., description="Virgülle ayrılmış ticker listesi (2-5)"), current_user: dict = Depends(get_current_user)):
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]

    if len(ticker_list) < 2 or len(ticker_list) > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2 ile 5 arasında ticker gerekli.")

    # Her zaman güncel veri çek (fiyat, oran vb. sürekli değişiyor)
    from src.ingestion.bist_finance_client import fetch_and_store
    try:
        await asyncio.wait_for(
            asyncio.gather(*[asyncio.to_thread(fetch_and_store, t) for t in ticker_list]),
            timeout=FETCH_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("yfinance fetch timeout (compare): %s", ticker_list)
    except Exception as e:
        logger.warning("yfinance fetch hatası (compare): %s", e)

    if not DB_PATH.exists():
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Veritabanı oluşturulamadı.")

    conn = get_conn()
    try:
        metrics = {}
        for t in ticker_list:
            metrics[t] = build_ticker_metrics(conn, t)
    finally:
        conn.close()

    return {"tickers": ticker_list, "metrics": metrics}


# ── Compare Ask (chat) ──

class CompareAskRequest(BaseModel):
    question: str
    tickers: list[str]
    conversation_history: list[dict] = []


@router.post("/compare/ask")
async def compare_ask(request: CompareAskRequest, current_user: dict = Depends(get_current_user)):
    tickers = [t.strip().upper() for t in request.tickers if t.strip()]
    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Soru boş olamaz.")
    if len(tickers) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="En az 2 ticker gerekli.")

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(run_agent, question, tickers[0], request.conversation_history, tickers),
            timeout=AGENT_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.error("Agent timeout (compare): %s — %s", tickers, question[:80])
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="İstek zaman aşımına uğradı.")
    except Exception as e:
        logger.error("Agent hatası (compare): %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Sunucu hatası oluştu.")

    return {
        "answer": result["answer"],
        "tickers": tickers,
        "sub_tasks": result["sub_tasks"],
        "retrieved_count": result["retrieved_count"],
        "retry_count": result["retry_count"],
        "critic_feedback": result["critic_feedback"],
    }
