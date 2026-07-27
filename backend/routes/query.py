"""
POST /api/ask — Soruyu LangGraph agent'a yönlendir.
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.auth import get_current_user

from src.agent.graph import run_agent

logger = logging.getLogger(__name__)

router = APIRouter()

AGENT_TIMEOUT = 120  # saniye


class AskRequest(BaseModel):
    question: str
    ticker: str
    conversation_history: list[dict] = []


@router.post("/ask")
async def ask(request: AskRequest, current_user: dict = Depends(get_current_user)):
    ticker = request.ticker.upper().strip()
    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Soru boş olamaz.")

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(run_agent, question, ticker, request.conversation_history),
            timeout=AGENT_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.error("Agent timeout: %s — %s", ticker, question[:80])
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="İstek zaman aşımına uğradı.")
    except Exception as e:
        logger.error("Agent hatası: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Sunucu hatası oluştu.")

    return {
        "answer": result["answer"],
        "ticker": ticker,
        "sub_tasks": result["sub_tasks"],
        "retrieved_count": result["retrieved_count"],
        "retry_count": result["retry_count"],
        "critic_feedback": result["critic_feedback"],
    }
