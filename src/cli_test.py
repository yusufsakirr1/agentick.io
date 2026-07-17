"""
Faz 2 uçtan uca test.
Hybrid RAG: soru tipine göre SQL + Vector retriever, Claude ile Türkçe cevap.

Kullanım:
    python -m src.cli_test --ticker THYAO --soru "THY'nin 2024 net marjı nedir?"
    python -m src.cli_test --ticker THYAO --soru "Yönetim büyüme stratejisi nedir?"
    python -m src.cli_test --ticker THYAO --soru "THYAO'nun son 3 yılda net marjı ve yönetim yorumu"
"""

import os
import argparse
from dotenv import load_dotenv

import anthropic

from src.retrievers.vector_retriever import search as vector_search
from src.retrievers.sql_retriever import search as sql_search

load_dotenv()

SYSTEM_PROMPT = """Sen bir Türk finansal araştırma asistanısın.
Sana verilen belge ve veri alıntılarını kullanarak kullanıcının sorusunu Türkçe olarak yanıtla.

Kurallar:
- Sadece verilen alıntılardaki bilgileri kullan, tahmin yapma.
- Her iddia için [Kaynak: ...] formatında kaynak göster.
- Sayısal veriler için SQL kaynağını, yönetim yorumları için KAP belge kaynağını belirt.
- Bilgi yoksa "Bu bilgi mevcut belgelerde bulunmuyor." de.
- Yanıtın sonuna "Bu bilgi yatırım tavsiyesi değildir." ekle."""

# Sayısal soru işaretleri — bu kelimeler varsa SQL retriever devreye girer
SQL_KEYWORDS = [
    "marj", "oran", "kâr", "kar", "gelir", "gider", "borç", "varlık",
    "özkaynak", "fiyat", "piyasa değeri", "f/k", "pd/dd", "ebitda",
    "nakit", "büyüme", "değişim", "kaç", "ne kadar", "yüzde", "%",
    "bilanço", "finansal sonuç", "net", "brüt",
]


def _route(soru: str) -> tuple[bool, bool]:
    """Sorunun SQL ve/veya vector retriever gerektirip gerektirmediğini belirle."""
    lower = soru.lower()
    use_sql = any(kw in lower for kw in SQL_KEYWORDS)
    # Sayısal değilse veya her ikisi de gerekliyse vector da çalışsın
    use_vector = not use_sql or any(kw in lower for kw in ["strateji", "yorum", "neden", "nasıl", "ne dedi", "açıkladı", "rapor"])
    # En az biri aktif olsun
    if not use_sql and not use_vector:
        use_vector = True
    return use_sql, use_vector


def ask(soru: str, ticker: str) -> str:
    use_sql, use_vector = _route(soru)
    context_parts = []

    if use_sql:
        print(f"\nSQL Retriever çalışıyor...")
        sql_results = sql_search(soru, ticker=ticker)
        if sql_results:
            for r in sql_results:
                context_parts.append(f"[Finansal Veri — {r['citation']}]\n{r['text']}")
            print(f"  SQL: {len(sql_results)} sonuç")
        else:
            print("  SQL: veri bulunamadı (önce bist_finance_client.py çalıştır)")

    if use_vector:
        print(f"\nVector Retriever çalışıyor (Qdrant)...")
        vector_results = vector_search(soru, ticker=ticker, top_k=4)
        if vector_results:
            for i, r in enumerate(vector_results, 1):
                context_parts.append(f"[KAP Belgesi {i} — {r['citation']}]\n{r['text']}")
            print(f"  Qdrant: {len(vector_results)} chunk bulundu")
        else:
            print("  Qdrant: chunk bulunamadı")

    if not context_parts:
        return "İlgili veri bulunamadı. Önce veri indexleme scriptlerini çalıştır."

    context = "\n\n---\n\n".join(context_parts)

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Belgeler:\n\n{context}\n\nSoru: {soru}"}
        ]
    )

    return message.content[0].text


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="THYAO")
    parser.add_argument("--soru", default="THYAO'nun son 3 yılda net marjı nasıl değişti?")
    args = parser.parse_args()

    print(f"\nTicker: {args.ticker}")
    print(f"Soru: {args.soru}")
    print("\n" + "=" * 60)

    cevap = ask(args.soru, args.ticker)
    print("\nCEVAP:")
    print(cevap)
