"""
Router Node — Alt görevleri paralel olarak ilgili retriever'lara yönlendirir.
asyncio.gather ile SQL ve vector retrieval eş zamanlı çalışır.
"""

import asyncio

from src.agent.state import AgentState
from src.retrievers.sql_retriever import search as sql_search
from src.retrievers.vector_retriever import search as vector_search
from src.retrievers.news_retriever import search as news_search

TASK_TIMEOUT = 30  # Her retriever task'ı için maks saniye


async def router_node(state: AgentState) -> dict:
    retry_count = state.get("retry_count", 0)
    top_k = 4 + (retry_count * 4)  # retry'da daha fazla sonuç al

    async def run_task(task: dict) -> list[dict]:
        query = task["query"]
        task_type = task["type"]
        task_ticker = task.get("ticker", state["ticker"])  # per-task ticker desteği
        try:
            if task_type == "sql":
                results = await asyncio.to_thread(sql_search, query, task_ticker)
                # SQL boş döndüyse → yfinance'den çek, tekrar dene
                if not results:
                    from src.ingestion.bist_finance_client import fetch_and_store
                    print(f"  SQL boş döndü, yfinance'den çekiliyor: {task_ticker}")
                    await asyncio.to_thread(fetch_and_store, task_ticker)
                    results = await asyncio.to_thread(sql_search, query, task_ticker)
                return results
            elif task_type == "vector":
                return await asyncio.to_thread(
                    vector_search, query, task_ticker, top_k
                )
            elif task_type == "news":
                return await asyncio.to_thread(
                    news_search, query, task_ticker, top_k
                )
        except Exception as e:
            print(f"  Retrieval hatası ({task_type}, {task_ticker}): {e}")
            return []
        return []

    async def run_task_with_timeout(task: dict) -> list[dict]:
        try:
            return await asyncio.wait_for(run_task(task), timeout=TASK_TIMEOUT)
        except asyncio.TimeoutError:
            task_type = task["type"]
            task_ticker = task.get("ticker", state["ticker"])
            print(f"  Timeout ({task_type}, {task_ticker}): {TASK_TIMEOUT}s aşıldı, atlanıyor")
            return []

    tasks = [run_task_with_timeout(t) for t in state["sub_tasks"]]
    results = await asyncio.gather(*tasks)

    # Daha önce eklenen chunk'ların text'lerini set'e al
    existing_texts = {r["text"] for r in state.get("retrieved", [])}

    new_results = []
    for result_list in results:
        for item in result_list:
            if item["text"] not in existing_texts:
                new_results.append(item)
                existing_texts.add(item["text"])

    return {
        "retrieved": new_results,
        "retry_count": retry_count + 1,
    }
