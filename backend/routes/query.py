"""
POST /api/ask — Soruyu LangGraph agent'a yönlendir.
"""

import asyncio

from fastapi import APIRouter
from pydantic import BaseModel

from src.agent.graph import run_agent

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    ticker: str
    conversation_history: list[dict] = []


@router.post("/ask")
async def ask(request: AskRequest):
    ticker = request.ticker.upper().strip()
    question = request.question.strip()

    if not question:
        return {"error": "Soru boş olamaz."}

    result = await asyncio.to_thread(
        run_agent, question, ticker, request.conversation_history
    )

    return {
        "answer": result["answer"],
        "ticker": ticker,
        "sub_tasks": result["sub_tasks"],
        "retrieved_count": result["retrieved_count"],
        "retry_count": result["retry_count"],
        "critic_feedback": result["critic_feedback"],
    }
