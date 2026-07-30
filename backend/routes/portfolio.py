"""
Portföy endpoint'leri:
  POST /api/portfolio/metrics — Portföy metrikleri, sektör dağılımı, uyarılar
  POST /api/portfolio/ask     — Portföy hakkında AI soru-cevap
  POST /api/portfolio/news    — Portföy hisselerine ait haberler
"""

import asyncio
import logging
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.constants import validate_tickers
from backend.rate_limit import enforce_rate_limit
from backend.services.metrics_utils import (
    get_conn, build_ticker_metrics, fetch_dividends, DB_PATH,
)

from src.agent.graph import run_agent

logger = logging.getLogger(__name__)

router = APIRouter()

FETCH_TIMEOUT = 60   # saniye — yfinance veri çekme
AGENT_TIMEOUT = 120  # saniye — LLM agent

# Konsantrasyon eşikleri
HOLDING_CONCENTRATION_THRESHOLD = 30   # %
SECTOR_CONCENTRATION_THRESHOLD = 40    # %
MAX_DIVIDEND_RESULTS = 20
MAX_NEWS_RESULTS = 20
MAX_PORTFOLIO_TICKERS = 30   # BIST-30 tamamı sığar
NEWS_PER_TICKER = 5


# ── Request Models ──

class HoldingInput(BaseModel):
    ticker: str
    shares: float
    avgCost: float


class PortfolioMetricsRequest(BaseModel):
    holdings: list[HoldingInput]


class PortfolioAskRequest(BaseModel):
    question: str
    tickers: list[str]
    conversation_history: list[dict] = []


class PortfolioNewsRequest(BaseModel):
    tickers: list[str]


# ── POST /portfolio/metrics ──

@router.post("/portfolio/metrics")
async def portfolio_metrics(request: PortfolioMetricsRequest, current_user: dict = Depends(enforce_rate_limit)):
    if not request.holdings:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="En az 1 holding gerekli.")

    validated = validate_tickers(
        [h.ticker for h in request.holdings], min_count=1, max_count=MAX_PORTFOLIO_TICKERS
    )
    tickers = list(dict.fromkeys(validated))   # tekrarları at, sırayı koru

    # Güncel veri çek
    from src.ingestion.bist_finance_client import fetch_and_store
    try:
        await asyncio.wait_for(
            asyncio.gather(*[asyncio.to_thread(fetch_and_store, t) for t in tickers]),
            timeout=FETCH_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("yfinance fetch timeout (portfolio): %s", tickers)
    except Exception as e:
        logger.warning("yfinance fetch hatası (portfolio): %s", e)

    if not DB_PATH.exists():
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Veritabanı oluşturulamadı.")

    conn = get_conn()
    try:
        # Per-ticker metrikleri topla
        ticker_data = {}
        for t in tickers:
            ticker_data[t] = build_ticker_metrics(conn, t)

        # Per-holding hesaplamalar
        holdings_result = []
        total_value = 0.0
        total_cost = 0.0

        for h in request.holdings:
            t = h.ticker.strip().upper()
            data = ticker_data.get(t, {})
            current_price = data.get("current_price") or 0
            market_value = current_price * h.shares
            cost_basis = h.avgCost * h.shares
            profit_loss = market_value - cost_basis
            profit_loss_pct = ((market_value / cost_basis) - 1) * 100 if cost_basis > 0 else 0

            total_value += market_value
            total_cost += cost_basis

            holdings_result.append({
                "ticker": t,
                "shares": h.shares,
                "avgCost": h.avgCost,
                "currentPrice": current_price,
                "marketValue": market_value,
                "costBasis": cost_basis,
                "profitLoss": profit_loss,
                "profitLossPct": profit_loss_pct,
                "weight": 0,  # hesaplanacak
                "sector": data.get("sector") or "Bilinmeyen",
                "pe_ratio": data.get("pe_ratio"),
                "dividend_yield": data.get("dividend_yield"),
                "net_margin": data.get("net_margin"),
            })

        # Ağırlık hesapla
        for h in holdings_result:
            h["weight"] = (h["marketValue"] / total_value * 100) if total_value > 0 else 0

        # Sektör dağılımı
        sector_map: dict[str, dict] = defaultdict(lambda: {"weight": 0.0, "tickers": []})
        for h in holdings_result:
            s = h["sector"]
            sector_map[s]["weight"] += h["weight"]
            if h["ticker"] not in sector_map[s]["tickers"]:
                sector_map[s]["tickers"].append(h["ticker"])

        sector_allocation = [
            {"sector": s, "weight": round(d["weight"], 1), "tickers": d["tickers"]}
            for s, d in sorted(sector_map.items(), key=lambda x: -x[1]["weight"])
        ]

        # Konsantrasyon uyarıları
        warnings = []
        for h in holdings_result:
            if h["weight"] > HOLDING_CONCENTRATION_THRESHOLD:
                warnings.append(f"{h['ticker']} portföyün %{h['weight']:.1f}'ini oluşturuyor (>%{HOLDING_CONCENTRATION_THRESHOLD})")
        for sa in sector_allocation:
            if sa["weight"] > SECTOR_CONCENTRATION_THRESHOLD:
                warnings.append(f"{sa['sector']} sektörü portföyün %{sa['weight']:.1f}'ini oluşturuyor (>%{SECTOR_CONCENTRATION_THRESHOLD})")

        # Ağırlıklı ortalamalar
        weighted_pe = 0.0
        weighted_div = 0.0
        weighted_margin = 0.0
        pe_total_w = 0.0
        div_total_w = 0.0
        margin_total_w = 0.0

        for h in holdings_result:
            w = h["weight"] / 100
            if h.get("pe_ratio"):
                weighted_pe += h["pe_ratio"] * w
                pe_total_w += w
            if h.get("dividend_yield"):
                weighted_div += h["dividend_yield"] * w
                div_total_w += w
            if h.get("net_margin"):
                weighted_margin += h["net_margin"] * w
                margin_total_w += w

        # Temettü takvimi
        all_dividends = []
        for t in tickers:
            divs = fetch_dividends(conn, t)
            all_dividends.extend(divs)
        all_dividends.sort(key=lambda d: d.get("ex_date", ""), reverse=True)

    finally:
        conn.close()

    total_profit_loss = total_value - total_cost
    total_profit_loss_pct = ((total_value / total_cost) - 1) * 100 if total_cost > 0 else 0

    return {
        "holdings": holdings_result,
        "summary": {
            "totalValue": round(total_value, 2),
            "totalCost": round(total_cost, 2),
            "totalProfitLoss": round(total_profit_loss, 2),
            "totalProfitLossPct": round(total_profit_loss_pct, 2),
            "weightedPE": round(weighted_pe / pe_total_w, 2) if pe_total_w > 0 else None,
            "weightedDividendYield": round(weighted_div / div_total_w, 2) if div_total_w > 0 else None,
            "weightedNetMargin": round(weighted_margin / margin_total_w, 2) if margin_total_w > 0 else None,
        },
        "sectorAllocation": sector_allocation,
        "warnings": warnings,
        "dividends": all_dividends[:MAX_DIVIDEND_RESULTS],
    }


# ── POST /portfolio/ask ──

@router.post("/portfolio/ask")
async def portfolio_ask(request: PortfolioAskRequest, current_user: dict = Depends(enforce_rate_limit)):
    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Soru boş olamaz.")

    tickers = validate_tickers(request.tickers, min_count=1, max_count=MAX_PORTFOLIO_TICKERS)

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                run_agent, question, tickers[0], request.conversation_history, tickers if len(tickers) > 1 else None
            ),
            timeout=AGENT_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.error("Agent timeout (portfolio): %s — %s", tickers, question[:80])
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="İstek zaman aşımına uğradı.")
    except Exception as e:
        logger.error("Agent hatası (portfolio): %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Sunucu hatası oluştu.")

    return {
        "answer": result["answer"],
        "tickers": tickers,
        "sub_tasks": result["sub_tasks"],
        "retrieved_count": result["retrieved_count"],
        "retry_count": result["retry_count"],
        "critic_feedback": result["critic_feedback"],
    }


# ── POST /portfolio/news ──

@router.post("/portfolio/news")
async def portfolio_news(request: PortfolioNewsRequest, current_user: dict = Depends(enforce_rate_limit)):
    tickers = validate_tickers(request.tickers, min_count=1, max_count=MAX_PORTFOLIO_TICKERS)

    from src.ingestion.news_client import fetch_news_if_stale, search_news_for_ticker

    # Haberleri tazele
    fetch_news_if_stale()

    all_articles = []
    seen_links: set[str] = set()

    for t in tickers:
        # Ticker tag'i → bulunamazsa şirket anahtar kelimeleri (alakasız haber getirmez)
        articles = search_news_for_ticker(t, top_k=NEWS_PER_TICKER)

        for a in articles:
            link = a.get("link", "")
            if link and link in seen_links:
                continue
            seen_links.add(link)
            a["ticker"] = t
            all_articles.append(a)

    # Tarihe göre sırala
    all_articles.sort(key=lambda a: a.get("published_at", ""), reverse=True)

    return {
        "tickers": tickers,
        "count": len(all_articles),
        "articles": all_articles[:MAX_NEWS_RESULTS],
    }
