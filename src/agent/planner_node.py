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
- "news": Güncel haberler, son gelişmeler, piyasa haberleri, şirket duyuruları, sektör haberleri

Ticker: {ticker}

JSON formatında döndür, başka açıklama ekleme:
{{
  "standalone_question": "...",
  "sub_tasks": [
    {{"query": "...", "type": "sql"}},
    {{"query": "...", "type": "vector"}}
  ]
}}"""


PLANNER_PROMPT_MULTI = """Sen bir finansal araştırma asistanısın. Birden fazla şirketi karşılaştırman isteniyor.

{history_section}Kullanıcının Yeni Sorusu: {question}

Karşılaştırılacak şirketler: {tickers}

{feedback_section}Adım 1 — Soruyu bağımsızlaştır:
Eğer soru sohbet geçmişine referans içeriyorsa, tam ve bağımsız yeniden yaz.

Adım 2 — Her şirket için ayrı alt görevler üret:
- "sql": Sayısal finansal veriler (gelir, kâr, marj, oran, büyüme, bilanço, nakit akış, fiyat)
- "vector": Nitel bilgiler (strateji, yönetim yorumları, risk faktörleri, faaliyet açıklamaları)
- "news": Güncel haberler, son gelişmeler, piyasa haberleri

Her alt göreve "ticker" alanı ekle.

JSON formatında döndür, başka açıklama ekleme:
{{
  "standalone_question": "...",
  "sub_tasks": [
    {{"query": "THYAO net marjı", "type": "sql", "ticker": "THYAO"}},
    {{"query": "TUPRS net marjı", "type": "sql", "ticker": "TUPRS"}},
    {{"query": "THYAO stratejisi", "type": "vector", "ticker": "THYAO"}}
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
    tickers = state.get("tickers", [state["ticker"]])
    is_multi = len(tickers) > 1

    feedback_section = ""
    if feedback and feedback != "SUFFICIENT" and retry > 0:
        feedback_section = f"Not: Önceki arama yetersiz bulundu: {feedback}\nDaha geniş veya farklı sorgular üret.\n\n"

    if is_multi:
        prompt_content = PLANNER_PROMPT_MULTI.format(
            tickers=", ".join(tickers),
            question=state["question"],
            history_section=_format_history(history),
            feedback_section=feedback_section,
        )
    else:
        prompt_content = PLANNER_PROMPT.format(
            ticker=state["ticker"],
            question=state["question"],
            history_section=_format_history(history),
            feedback_section=feedback_section,
        )

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024 if is_multi else 512,
        messages=[{
            "role": "user",
            "content": prompt_content,
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
        if is_multi:
            sub_tasks = []
            for t in tickers:
                sub_tasks.append({"query": state["question"], "type": "sql", "ticker": t})
                sub_tasks.append({"query": state["question"], "type": "vector", "ticker": t})
                sub_tasks.append({"query": state["question"], "type": "news", "ticker": t})
        else:
            sub_tasks = [
                {"query": state["question"], "type": "sql"},
                {"query": state["question"], "type": "vector"},
                {"query": state["question"], "type": "news"},
            ]
        standalone = state["question"]

    return {"sub_tasks": sub_tasks, "standalone_question": standalone}
