"""
Router Node — Alt görevleri paralel olarak ilgili retriever'lara yönlendirir.
asyncio.gather ile SQL ve vector retrieval eş zamanlı çalışır.
"""

import asyncio

from src.agent.state import AgentState
from src.retrievers.sql_retriever import search as sql_search
from src.retrievers.vector_retriever import search as vector_search


async def router_node(state: AgentState) -> dict:
    retry_count = state.get("retry_count", 0)
    top_k = 4 + (retry_count * 4)  # retry'da daha fazla sonuç al

    async def run_task(task: dict) -> list[dict]:
        query = task["query"]
        task_type = task["type"]
        try:
            if task_type == "sql":
                return await asyncio.to_thread(sql_search, query, state["ticker"])
            elif task_type == "vector":
                return await asyncio.to_thread(
                    vector_search, query, state["ticker"], top_k
                )
        except Exception as e:
            return [{"text": f"Retrieval hatası ({task_type}): {e}", "citation": "hata", "score": 0.0}]
        return []

    tasks = [run_task(t) for t in state["sub_tasks"]]
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
