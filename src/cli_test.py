"""
Faz 1 uçtan uca test.
Naive RAG: soru → embed → Qdrant'ta ara → Claude'a ver → cevap.

Kullanım:
    python -m src.cli_test --ticker THYAO --soru "THY'nin 2024 yolcu gelirleri nedir?"
"""

import os
import argparse
from dotenv import load_dotenv

import anthropic

from src.retrievers.vector_retriever import search

load_dotenv()

SYSTEM_PROMPT = """Sen bir Türk finansal araştırma asistanısın.
Sana verilen KAP belgesi alıntılarını kullanarak kullanıcının sorusunu Türkçe olarak yanıtla.

Kurallar:
- Sadece verilen alıntılardaki bilgileri kullan, tahmin yapma.
- Her iddia için [Kaynak: ...] formatında kaynak göster.
- Bilgi yoksa "Bu bilgi mevcut belgelerde bulunmuyor." de.
- Yanıtın sonuna "Bu bilgi yatırım tavsiyesi değildir." ekle."""


def ask(soru: str, ticker: str) -> str:
    # 1. Qdrant'tan ilgili chunk'ları getir
    print(f"\nQdrant'ta aranıyor: '{soru}'")
    chunks = search(soru, ticker=ticker, top_k=5)

    if not chunks:
        return "İlgili belge bulunamadı. Önce build_vector_index.py çalıştır."

    print(f"{len(chunks)} chunk bulundu.")

    # 2. Context oluştur
    context_parts = []
    for i, c in enumerate(chunks, 1):
        context_parts.append(
            f"[Alıntı {i} — {c['citation']}]\n{c['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # 3. Claude'a gönder
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
    parser.add_argument("--soru", default="Şirketin 2024 yılındaki temel finansal sonuçları nelerdir?")
    args = parser.parse_args()

    print(f"\nTicker: {args.ticker}")
    print(f"Soru: {args.soru}")
    print("\n" + "="*60)

    cevap = ask(args.soru, args.ticker)
    print("\nCEVAP:")
    print(cevap)
