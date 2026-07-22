"""
Qdrant'ta semantic search yapar.
"""

import os
from dotenv import load_dotenv

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from src.ingestion.build_vector_index import COLLECTION_NAME, EMBED_MODEL

load_dotenv()

_model = None

def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def search(query: str, ticker: str | None = None, top_k: int = 5) -> list[dict]:
    """
    Soruya en yakın chunk'ları döndürür.

    Args:
        query:  Kullanıcının sorusu (Türkçe)
        ticker: Filtre için hisse kodu (ör. "THYAO"). None ise tüm collection'da arar.
        top_k:  Kaç sonuç dönsün

    Returns:
        [{"text": ..., "ticker": ..., "page": ..., "section": ..., "score": ...}]
    """
    model = _get_model()
    query_embedding = model.encode([query])[0].tolist()

    client = QdrantClient(
        url=os.environ["QDRANT_URL"],
        api_key=os.environ["QDRANT_API_KEY"],
        timeout=15,
    )

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
            "text": r.payload["text"],
            "ticker": r.payload["ticker"],
            "page": r.payload["page"],
            "section": r.payload["section"],
            "source_file": r.payload["source_file"],
            "score": round(r.score, 4),
            "citation": f"KAP — {r.payload['ticker']} Faaliyet Raporu, s.{r.payload['page']} ({r.payload['section']})",
        }
        for r in response.points
    ]


if __name__ == "__main__":
    results = search("yolcu gelirleri ve kargo geliri", ticker="THYAO")
    for r in results:
        print(f"\n[{r['citation']}] (skor: {r['score']})")
        print(r["text"][:300])
