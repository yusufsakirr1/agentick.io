"""
Planner Node — Soruyu analiz edip alt görevlere böler.
Her alt görev için tip (sql/vector) belirler.
"""

import os
import json
import re

import anthropic
from dotenv import load_dotenv

from src.agent.state import AgentState

load_dotenv()

PLANNER_PROMPT = """Sen bir finansal araştırma asistanısın.

{history_section}Kullanıcının Yeni Sorusu: {question}

{feedback_section}Adım 1 — Soruyu bağımsızlaştır:
Eğer soru "peki bu?", "önceki yıla göre?", "neden?" gibi sohbet geçmişine referans içeriyorsa,
geçmişe bakarak soruyu tam ve bağımsız bir şekilde yeniden yaz.
Bağımsızsa olduğu gibi kullan.

Adım 2 — Hangi kaynaktan veri alınacağına karar ver:
- "sql": Sayısal finansal veriler (gelir, kâr, marj, oran, büyüme, bilanço, nakit akış, fiyat)
- "vector": Nitel bilgiler (strateji, yönetim yorumları, risk faktörleri, faaliyet açıklamaları)

Ticker: {ticker}

JSON formatında döndür, başka açıklama ekleme:
{{
  "standalone_question": "...",
  "sub_tasks": [
    {{"query": "...", "type": "sql"}},
    {{"query": "...", "type": "vector"}}
  ]
}}"""


def _format_history(history: list[dict]) -> str:
    if not history:
        return ""
    lines = []
    for msg in history[-6:]:  # son 3 tur (6 mesaj)
        role = "Kullanıcı" if msg["role"] == "user" else "Asistan"
        content = msg["content"][:300]  # çok uzun olmasın
        lines.append(f"{role}: {content}")
    return "Sohbet Geçmişi:\n" + "\n".join(lines) + "\n\n"


def planner_node(state: AgentState) -> dict:
    feedback = state.get("critic_feedback", "")
    retry = state.get("retry_count", 0)
    history = state.get("conversation_history", [])

    feedback_section = ""
    if feedback and feedback != "SUFFICIENT" and retry > 0:
        feedback_section = f"Not: Önceki arama yetersiz bulundu: {feedback}\nDaha geniş veya farklı sorgular üret.\n\n"

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": PLANNER_PROMPT.format(
                ticker=state["ticker"],
                question=state["question"],
                history_section=_format_history(history),
                feedback_section=feedback_section,
            )
        }]
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw)

    try:
        data = json.loads(raw)
        sub_tasks = data.get("sub_tasks", [])
        standalone = data.get("standalone_question", state["question"])
    except json.JSONDecodeError:
        sub_tasks = [
            {"query": state["question"], "type": "sql"},
            {"query": state["question"], "type": "vector"},
        ]
        standalone = state["question"]

    return {"sub_tasks": sub_tasks, "standalone_question": standalone}
