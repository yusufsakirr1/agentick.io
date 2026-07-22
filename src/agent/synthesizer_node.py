"""
Synthesizer Node — Toplanan tüm verileri Türkçe, kaynaklı bir cevaba dönüştürür.
"""

import os

import anthropic
from dotenv import load_dotenv

from src.agent.state import AgentState

load_dotenv()

SYSTEM_PROMPT = """Sen bir Türk finansal araştırma asistanısın.
Sana verilen belge ve veri alıntılarını kullanarak kullanıcının sorusunu Türkçe olarak yanıtla.

Yazım kuralları:
- Sade, akıcı Türkçe kullan. Emoji kullanma.
- Markdown tablo kullanma; sayısal verileri düz metin veya madde listesiyle ver.
- Başlık (##) kullanma; gerekirse kalın metin (**...**) ile vurgula.
- Kısa ve öz yaz. Gereksiz tekrar etme.
- Her somut iddia için parantez içinde kaynak göster: (Kaynak: ...)
- Sadece verilen alıntılardaki bilgileri kullan, tahmin yapma.
- Bilgi yoksa "Bu bilgi mevcut belgelerde bulunmuyor." de.
- Yanıtın en sonuna kısa bir satır ekle: "Bu bilgi yatırım tavsiyesi değildir." """

SYSTEM_PROMPT_COMPARE = """Sen bir Türk finansal araştırma asistanısın. Birden fazla şirketi karşılaştırmalı analiz ediyorsun.

Sana verilen belge ve veri alıntılarını kullanarak kullanıcının karşılaştırma sorusunu Türkçe olarak yanıtla.

Yazım kuralları:
- Sade, akıcı Türkçe kullan. Emoji kullanma.
- Markdown tablo kullanma; sayısal verileri düz metin veya madde listesiyle ver.
- Başlık (##) kullanma; gerekirse kalın metin (**...**) ile vurgula.
- Kısa ve öz yaz. Gereksiz tekrar etme.
- Her somut iddia için parantez içinde kaynak göster: (Kaynak: ...)
- Sadece verilen alıntılardaki bilgileri kullan, tahmin yapma.
- Bilgi yoksa "Bu bilgi mevcut belgelerde bulunmuyor." de.

Karşılaştırma kuralları:
- Her şirketi ayrı ayrı ele al, ardından karşılaştırmalı bir özet sun.
- Güçlü ve zayıf yönleri belirt.
- Sayısal verilerde farkları vurgula.
- Yanıtın en sonuna kısa bir satır ekle: "Bu bilgi yatırım tavsiyesi değildir." """


MAX_SOURCES = 12

def _build_context(retrieved: list[dict]) -> str:
    # Skoru yüksek olanları önce al, max 12 kaynak
    sorted_results = sorted(retrieved, key=lambda r: r.get("score", 0), reverse=True)
    top = sorted_results[:MAX_SOURCES]
    parts = []
    for i, r in enumerate(top, 1):
        citation = r.get("citation", f"Kaynak {i}")
        text = r.get("text", "")
        parts.append(f"[{citation}]\n{text}")
    return "\n\n---\n\n".join(parts)


def synthesizer_node(state: AgentState) -> dict:
    retrieved = state.get("retrieved", [])
    if not retrieved:
        return {"final_answer": "İlgili veri bulunamadı. Lütfen önce PDF yükleyin ve finansal veri çekin."}

    context = _build_context(retrieved)
    tickers = state.get("tickers", [state["ticker"]])
    is_multi = len(tickers) > 1
    system_prompt = SYSTEM_PROMPT_COMPARE if is_multi else SYSTEM_PROMPT

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500 if is_multi else 1500,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Belgeler:\n\n{context}\n\nSoru: {state['question']}"
        }]
    )

    return {"final_answer": response.content[0].text}
