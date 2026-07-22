"""
POST /api/fetch-data — Ticker için yfinance verilerini çekip SQLite'a yazar.
"""

import asyncio

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.auth import get_current_user

from src.ingestion.bist_finance_client import fetch_and_store

router = APIRouter()


class FetchRequest(BaseModel):
    ticker: str


@router.post("/fetch-data")
async def fetch_data(request: FetchRequest, current_user: dict = Depends(get_current_user)):
    ticker = request.ticker.upper().strip()
    if not ticker:
        return {"error": "Ticker boş olamaz."}
    await asyncio.to_thread(fetch_and_store, ticker)
    return {"status": "ok", "ticker": ticker}
