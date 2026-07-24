"""
Karşılaştırma endpoint'leri:
  GET  /api/compare/metrics  — 2-5 ticker için metrik karşılaştırması (LLM gerektirmez)
  POST /api/compare/ask      — Karşılaştırma chat sorusu (multi-ticker agent)
"""

import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.auth import get_current_user
from backend.services.metrics_utils import get_conn, build_ticker_metrics, DB_PATH

from src.agent.graph import run_agent

router = APIRouter()


@router.get("/compare/metrics")
async def compare_metrics(tickers: str = Query(..., description="Virgülle ayrılmış ticker listesi (2-5)"), current_user: dict = Depends(get_current_user)):
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]

    if len(ticker_list) < 2 or len(ticker_list) > 5:
        return {"error": "2 ile 5 arasında ticker gerekli."}

    # Her zaman güncel veri çek (fiyat, oran vb. sürekli değişiyor)
    from src.ingestion.bist_finance_client import fetch_and_store
    await asyncio.gather(*[asyncio.to_thread(fetch_and_store, t) for t in ticker_list])

    if not DB_PATH.exists():
        return {"error": "Veritabanı oluşturulamadı."}

    conn = get_conn()
    metrics = {}
    for t in ticker_list:
        metrics[t] = build_ticker_metrics(conn, t)
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
        return {"error": "Soru boş olamaz."}
    if len(tickers) < 2:
        return {"error": "En az 2 ticker gerekli."}

    try:
        result = await asyncio.to_thread(
            run_agent, question, tickers[0], request.conversation_history, tickers
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Agent hatası: {str(e)}"}

    return {
        "answer": result["answer"],
        "tickers": tickers,
        "sub_tasks": result["sub_tasks"],
        "retrieved_count": result["retrieved_count"],
        "retry_count": result["retry_count"],
        "critic_feedback": result["critic_feedback"],
    }
