"""
LangGraph StateGraph tanımı.

Akış: PLANNER → ROUTER → CRITIC → (retry veya SYNTHESIZER) → END
"""

import asyncio

from langgraph.graph import StateGraph, END

from src.agent.state import AgentState
from src.agent.planner_node import planner_node
from src.agent.router_node import router_node
from src.agent.critic_node import critic_node, should_continue
from src.agent.synthesizer_node import synthesizer_node


def _run_async(coro):
    """Sync context'te async coroutine çalıştır."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def _router_node_sync(state: AgentState) -> dict:
    """Router node'u sync wrapper içinde çalıştır."""
    return _run_async(router_node(state))


def _build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("router", _router_node_sync)
    workflow.add_node("critic", critic_node)
    workflow.add_node("synthesizer", synthesizer_node)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "router")
    workflow.add_edge("router", "critic")
    workflow.add_conditional_edges(
        "critic",
        should_continue,
        {
            "retry": "planner",   # Planner yeni sorgular üretir
            "synthesize": "synthesizer",
        }
    )
    workflow.add_edge("synthesizer", END)

    return workflow.compile()


_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


def run_agent(question: str, ticker: str, conversation_history: list[dict] | None = None) -> dict:
    """
    LangGraph agent'ı çalıştırır ve sonucu döndürür.

    Returns:
        {
            "answer": str,
            "sub_tasks": list,
            "retrieved_count": int,
            "retry_count": int,
        }
    """
    graph = _get_graph()

    initial_state: AgentState = {
        "question": question,
        "ticker": ticker.upper(),
        "conversation_history": conversation_history or [],
        "standalone_question": question,
        "sub_tasks": [],
        "retrieved": [],
        "critic_feedback": "",
        "retry_count": 0,
        "final_answer": "",
    }

    result = graph.invoke(initial_state)

    return {
        "answer": result.get("final_answer", ""),
        "sub_tasks": result.get("sub_tasks", []),
        "retrieved_count": len(result.get("retrieved", [])),
        "retry_count": result.get("retry_count", 0),
        "critic_feedback": result.get("critic_feedback", ""),
    }
