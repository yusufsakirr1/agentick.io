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

Yasal uyumluluk kuralları (SPK düzenlemesi — kesinlikle uy):
- Asla "al", "sat", "tut", "bu hisseyi almanızı öneririm", "yatırım yapın", "portföyünüze ekleyin" gibi alım-satım yönlendirmesi yapma.
- Asla "bu hisse ucuz/pahalı", "fırsat", "kaçırmayın", "riskli değil" gibi değer yargısı içeren ifadeler kullanma.
- Asla hedef fiyat verme veya gelecekteki fiyat tahmini yapma.
- Sadece verileri ve oranları sun, yorumu kullanıcıya bırak.
- Karşılaştırmalarda "X daha iyi" yerine "X'in net marjı daha yüksek" gibi objektif ifadeler kullan.
- Yanıtın en sonuna mutlaka şu satırı ekle: "Bu içerik yalnızca bilgilendirme amaçlıdır, yatırım tavsiyesi niteliği taşımaz. Yatırım kararlarınızı almadan önce lisanslı bir yatırım danışmanına başvurunuz." """

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
- Sayısal verilerde farkları objektif olarak belirt.
- "X daha iyi" yerine "X'in net marjı daha yüksek" gibi ölçülebilir ifadeler kullan.

Yasal uyumluluk kuralları (SPK düzenlemesi — kesinlikle uy):
- Asla "al", "sat", "tut", "bu hisseyi almanızı öneririm", "yatırım yapın", "portföyünüze ekleyin" gibi alım-satım yönlendirmesi yapma.
- Asla "bu hisse ucuz/pahalı", "fırsat", "kaçırmayın", "riskli değil" gibi değer yargısı içeren ifadeler kullanma.
- Asla hedef fiyat verme veya gelecekteki fiyat tahmini yapma.
- Asla "X hissesini tercih edin", "X daha cazip" gibi yönlendirici sonuçlar çıkarma.
- Sadece verileri ve oranları sun, tercih ve kararı kullanıcıya bırak.
- Yanıtın en sonuna mutlaka şu satırı ekle: "Bu içerik yalnızca bilgilendirme amaçlıdır, yatırım tavsiyesi niteliği taşımaz. Yatırım kararlarınızı almadan önce lisanslı bir yatırım danışmanına başvurunuz." """


MAX_SOURCES = 12
SNIPPET_LENGTH = 240


def _select_sources(retrieved: list[dict]) -> list[dict]:
    """Skoru yüksek olanları önce al, max 12 kaynak."""
    return sorted(retrieved, key=lambda r: r.get("score", 0), reverse=True)[:MAX_SOURCES]


def _build_context(top: list[dict]) -> str:
    parts = []
    for i, r in enumerate(top, 1):
        citation = r.get("citation", f"Kaynak {i}")
        text = r.get("text", "")
        parts.append(f"[{citation}]\n{text}")
    return "\n\n---\n\n".join(parts)


def _to_source(item: dict) -> dict:
    """
    Retriever çıktısını frontend'in gösterebileceği sade bir kaynak kaydına çevirir.
    Kullanıcı, cevabın hangi dosya/sayfa/tablodan geldiğini burada görür.
    """
    text = (item.get("text") or "").strip()
    snippet = text[:SNIPPET_LENGTH] + ("…" if len(text) > SNIPPET_LENGTH else "")
    source_type = item.get("source_type") or "vector"

    source: dict = {
        "type": source_type,
        "citation": item.get("citation", ""),
        "ticker": item.get("ticker", ""),
        "score": round(float(item.get("score") or 0), 4),
        "snippet": snippet,
    }

    if source_type == "vector":
        # KAP raporundan gelen metin chunk'ı — tek sayfa
        page = item.get("page")
        source["source_file"] = item.get("source_file") or None
        source["pages"] = [page] if page else []
        source["section"] = item.get("section") or None
    elif source_type == "pdf":
        # PDF'ten çıkarılmış tablo(lar) — birden fazla sayfa olabilir
        source["source_file"] = item.get("source_file") or None
        source["pages"] = item.get("pages") or []
    elif source_type == "news":
        source["title"] = item.get("title") or None
        source["link"] = item.get("link") or None
        source["published_at"] = item.get("published_at") or None
    elif source_type == "sql":
        source["tables"] = item.get("tables") or []
        source["period_range"] = item.get("period_range") or None

    return source


def build_source_list(retrieved: list[dict]) -> list[dict]:
    """Synthesizer'a verilen kaynakların UI için hazırlanmış listesi."""
    return [_to_source(item) for item in _select_sources(retrieved)]


def synthesizer_node(state: AgentState) -> dict:
    retrieved = state.get("retrieved", [])
    if not retrieved:
        return {
            "final_answer": "İlgili veri bulunamadı. Lütfen önce PDF yükleyin ve finansal veri çekin.",
            "used_sources": [],
        }

    top = _select_sources(retrieved)
    context = _build_context(top)
    tickers = state.get("tickers", [state["ticker"]])
    is_multi = len(tickers) > 1
    system_prompt = SYSTEM_PROMPT_COMPARE if is_multi else SYSTEM_PROMPT

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2500 if is_multi else 1500,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Belgeler:\n\n{context}\n\nSoru: {state['question']}"
        }]
    )

    return {
        "final_answer": response.content[0].text,
        "used_sources": [_to_source(item) for item in top],
    }
