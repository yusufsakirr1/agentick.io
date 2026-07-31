"""
Qdrant'ta semantic search yapar.
Singleton client + hata toleransı + env var validasyonu.
"""

import logging
import os
import threading

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Embedding modeli indexleme ile ortak singleton — iki ayrı kopya RAM'de tutulmasın
from src.ingestion.build_vector_index import COLLECTION_NAME, get_model

load_dotenv()

logger = logging.getLogger(__name__)

_client = None
_client_lock = threading.Lock()


def _get_client() -> QdrantClient | None:
    """Singleton Qdrant client. Env var eksikse None döner."""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                url = os.environ.get("QDRANT_URL")
                api_key = os.environ.get("QDRANT_API_KEY")
                if not url or not api_key:
                    logger.error("QDRANT_URL veya QDRANT_API_KEY tanımlı değil.")
                    return None
                _client = QdrantClient(url=url, api_key=api_key, timeout=15)
    return _client


def search(query: str, ticker: str | None = None, top_k: int = 5) -> list[dict]:
    """
    Soruya en yakın chunk'ları döndürür.

    Args:
        query:  Kullanıcının sorusu (Türkçe)
        ticker: Filtre için hisse kodu (ör. "THYAO"). None ise tüm collection'da arar.
        top_k:  Kaç sonuç dönsün

    Returns:
        [{"text": ..., "ticker": ..., "page": ..., "section": ..., "score": ...}]
        Hata durumunda boş liste döner.
    """
    try:
        client = _get_client()
        if client is None:
            return []

        model = get_model()
        query_embedding = model.encode([query])[0].tolist()

        query_filter = None
        if ticker:
            query_filter = Filter(
                must=[FieldCondition(key="ticker", match=MatchValue(value=ticker.upper()))]
            )

        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )

        return [
            {
                "text": r.payload.get("text", ""),
                "ticker": r.payload.get("ticker", ""),
                "page": r.payload.get("page", 0),
                "section": r.payload.get("section", "Genel"),
                "source_file": r.payload.get("source_file", ""),
                "chunk_index": r.payload.get("chunk_index"),
                "score": round(r.score, 4),
                "source_type": "vector",
                "citation": (
                    f"KAP — {r.payload.get('ticker', '')} Faaliyet Raporu, "
                    f"s.{r.payload.get('page', '?')} ({r.payload.get('section', 'Genel')})"
                ),
            }
            for r in response.points
        ]

    except Exception as e:
        logger.error("Qdrant search hatası: %s", e)
        return []


if __name__ == "__main__":
    results = search("yolcu gelirleri ve kargo geliri", ticker="THYAO")
    for r in results:
        print(f"\n[{r['citation']}] (skor: {r['score']})")
        print(r["text"][:300])
