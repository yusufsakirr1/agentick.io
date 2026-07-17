"""
Critic Node — Toplanan bilginin soruyu cevaplamaya yeterli olup olmadığını değerlendirir.
"""

import os

import anthropic
from dotenv import load_dotenv

from src.agent.state import AgentState

load_dotenv()

CRITIC_PROMPT = """Bir finansal araştırma sorusu için yeterli bilgi toplanıp toplanmadığını değerlendir.

Soru: {question}

Toplanan bilgi (ilk {sample_count} kaynak):
{retrieved_text}

Değerlendirme kriteri:
- Soruyla ilgili herhangi bir veri veya metin varsa → SUFFICIENT
- Hiçbir ilgili bilgi yoksa (tamamen boş veya sadece hata mesajları) → INSUFFICIENT

Eğer yeterliyse tam olarak şunu yaz: SUFFICIENT
Eğer yetersizse şunu yaz: INSUFFICIENT: [tek cümle neden]

Tek satır döndür, başka açıklama ekleme."""


CRITIC_SAMPLE = 6  # Critic'e gösterilecek max kaynak sayısı

def _format_retrieved(retrieved: list[dict]) -> tuple[str, int]:
    if not retrieved:
        return "Hiçbir veri bulunamadı.", 0
    sample = retrieved[:CRITIC_SAMPLE]
    parts = []
    for r in sample:
        citation = r.get("citation", "?")
        text = r.get("text", "")[:250]
        parts.append(f"[{citation}]\n{text}")
    return "\n\n".join(parts), len(sample)


def critic_node(state: AgentState) -> dict:
    retrieved_text, sample_count = _format_retrieved(state.get("retrieved", []))

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=64,
        messages=[{
            "role": "user",
            "content": CRITIC_PROMPT.format(
                question=state["question"],
                retrieved_text=retrieved_text,
                sample_count=sample_count,
            )
        }]
    )

    feedback = response.content[0].text.strip()
    return {"critic_feedback": feedback}


def should_continue(state: AgentState) -> str:
    feedback = state.get("critic_feedback", "")
    retry_count = state.get("retry_count", 0)

    if feedback.startswith("SUFFICIENT") or retry_count >= 3:
        return "synthesize"
    return "retry"
