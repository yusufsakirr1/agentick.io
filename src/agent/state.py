from typing import TypedDict, Annotated
import operator


class AgentState(TypedDict):
    question: str
    ticker: str
    conversation_history: list[dict]   # [{"role": "user"|"assistant", "content": "..."}]
    standalone_question: str           # Planner'ın yeniden yazdığı bağımsız soru
    sub_tasks: list[dict]              # [{"query": ..., "type": "sql"|"vector"}]
    retrieved: Annotated[list[dict], operator.add]  # akkümülatif retriever sonuçları
    critic_feedback: str               # "SUFFICIENT" veya "INSUFFICIENT: ..."
    retry_count: int
    final_answer: str
