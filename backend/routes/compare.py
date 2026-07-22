"""
Karşılaştırma endpoint'leri:
  GET  /api/compare/metrics  — 2-5 ticker için metrik karşılaştırması (LLM gerektirmez)
  POST /api/compare/ask      — Karşılaştırma chat sorusu (multi-ticker agent)
"""

import asyncio
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.agent.graph import run_agent

router = APIRouter()

DB_PATH = Path("data/bist_financials.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _fetch_latest_ratios(conn: sqlite3.Connection, ticker: str) -> dict:
    row = conn.execute(
        "SELECT * FROM ratios WHERE ticker = ? ORDER BY period_date DESC LIMIT 1",
        (ticker,),
    ).fetchone()
    return dict(row) if row else {}


def _fetch_latest_income(conn: sqlite3.Connection, ticker: str) -> dict:
    row = conn.execute(
        "SELECT * FROM income_statement WHERE ticker = ? ORDER BY period_date DESC LIMIT 1",
        (ticker,),
    ).fetchone()
    return dict(row) if row else {}


def _fetch_latest_balance(conn: sqlite3.Connection, ticker: str) -> dict:
    row = conn.execute(
        "SELECT * FROM balance_sheet WHERE ticker = ? ORDER BY period_date DESC LIMIT 1",
        (ticker,),
    ).fetchone()
    return dict(row) if row else {}


def _fetch_dividend_yield(conn: sqlite3.Connection, ticker: str, current_price: float | None) -> float | None:
    if not current_price:
        return None
    row = conn.execute(
        "SELECT SUM(amount) AS total FROM dividends WHERE ticker = ? AND ex_date >= date('now', '-1 year')",
        (ticker,),
    ).fetchone()
    total = row["total"] if row and row["total"] else 0
    if total and current_price > 0:
        return round((total / current_price) * 100, 2)
    return None


def _build_ticker_metrics(conn: sqlite3.Connection, ticker: str) -> dict:
    ratios = _fetch_latest_ratios(conn, ticker)
    income = _fetch_latest_income(conn, ticker)
    balance = _fetch_latest_balance(conn, ticker)
    current_price = ratios.get("current_price")
    dividend_yield = _fetch_dividend_yield(conn, ticker, current_price)

    return {
        "ticker": ticker,
        "current_price": current_price,
        "market_cap": ratios.get("market_cap"),
        "pe_ratio": ratios.get("pe_ratio"),
        "pb_ratio": ratios.get("pb_ratio"),
        "net_margin": ratios.get("net_margin"),
        "roe": ratios.get("roe"),
        "roa": ratios.get("roa"),
        "debt_to_equity": ratios.get("debt_to_equity"),
        "dividend_yield": dividend_yield,
        "revenue": income.get("revenue"),
        "net_income": income.get("net_income"),
        "ebitda": income.get("ebitda"),
        "total_assets": balance.get("total_assets"),
        "total_equity": balance.get("total_equity"),
        "total_debt": balance.get("total_debt"),
        "ratios_date": ratios.get("period_date"),
        "income_date": income.get("period_date"),
    }


@router.get("/compare/metrics")
async def compare_metrics(tickers: str = Query(..., description="Virgülle ayrılmış ticker listesi (2-5)")):
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]

    if len(ticker_list) < 2 or len(ticker_list) > 5:
        return {"error": "2 ile 5 arasında ticker gerekli."}

    # Her zaman güncel veri çek (fiyat, oran vb. sürekli değişiyor)
    from src.ingestion.bist_finance_client import fetch_and_store
    await asyncio.gather(*[asyncio.to_thread(fetch_and_store, t) for t in ticker_list])

    if not DB_PATH.exists():
        return {"error": "Veritabanı oluşturulamadı."}

    conn = _get_conn()
    metrics = {}
    for t in ticker_list:
        metrics[t] = _build_ticker_metrics(conn, t)
    conn.close()

    return {"tickers": ticker_list, "metrics": metrics}


# ── Compare Ask (chat) ──

class CompareAskRequest(BaseModel):
    question: str
    tickers: list[str]
    conversation_history: list[dict] = []


@router.post("/compare/ask")
async def compare_ask(request: CompareAskRequest):
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
