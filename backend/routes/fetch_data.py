"""
POST /api/fetch-data — Ticker için yfinance verilerini çekip SQLite'a yazar.
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.auth import get_current_user

from src.ingestion.bist_finance_client import fetch_and_store

logger = logging.getLogger(__name__)

router = APIRouter()

FETCH_TIMEOUT = 60  # saniye


class FetchRequest(BaseModel):
    ticker: str


@router.post("/fetch-data")
async def fetch_data(request: FetchRequest, current_user: dict = Depends(get_current_user)):
    ticker = request.ticker.upper().strip()
    if not ticker:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticker boş olamaz.")

    try:
        await asyncio.wait_for(
            asyncio.to_thread(fetch_and_store, ticker),
            timeout=FETCH_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.error("yfinance fetch timeout: %s", ticker)
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Veri çekme zaman aşımına uğradı.")
    except Exception as e:
        logger.error("yfinance fetch hatası (%s): %s", ticker, e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Veri çekme hatası.")

    return {"status": "ok", "ticker": ticker}
