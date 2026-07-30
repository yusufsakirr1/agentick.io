"""
PDF chunk'larını embedding'e çevirip Qdrant'a yazar.

Kullanım:
    python -m src.ingestion.build_vector_index --ticker THYAO --pdf data/raw/THYAO_xxxx.pdf
"""

import logging
import os
import argparse
import threading
import uuid
from pathlib import Path
from dotenv import load_dotenv

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue,
    FilterSelector,
)

from src.ingestion.pdf_chunker import chunk_pdf, Chunk

load_dotenv()

logger = logging.getLogger(__name__)

COLLECTION_NAME = "kap_filings"
VECTOR_SIZE = 768  # paraphrase-multilingual-mpnet-base-v2 boyutu
EMBED_MODEL = "paraphrase-multilingual-mpnet-base-v2"  # Türkçe destekli, ücretsiz

# Point ID'leri (ticker, dosya, chunk sırası) üçlüsünden deterministik üretilir.
# Böylece farklı PDF'lerin chunk'ları birbirinin üzerine yazmaz.
POINT_NAMESPACE = uuid.UUID("6f1b4c9e-5a3d-4f27-9c8b-2e1d0a7b3c45")

_model: SentenceTransformer | None = None
_model_lock = threading.Lock()


def get_model() -> SentenceTransformer:
    """
    Süreç genelinde tek bir SentenceTransformer örneği (thread-safe).
    Model ~1 GB RAM tuttuğu için her çağrıda yeniden yüklenmemeli.
    """
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                logger.info("Embedding modeli yükleniyor: %s (ilk seferde indirilir)", EMBED_MODEL)
                _model = SentenceTransformer(EMBED_MODEL)
    return _model


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        url=os.environ.get("QDRANT_URL", ""),
        api_key=os.environ.get("QDRANT_API_KEY", ""),
        timeout=60,
    )


def _point_id(ticker: str, source_file: str, chunk_index: int) -> str:
    return str(uuid.uuid5(POINT_NAMESPACE, f"{ticker}|{source_file}|{chunk_index}"))


def ensure_collection(client: QdrantClient):
    """Collection yoksa oluştur, payload index'lerini ekle."""
    from qdrant_client.models import PayloadSchemaType
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        logger.info("Collection oluşturuldu: %s", COLLECTION_NAME)
    else:
        logger.info("Collection zaten var: %s", COLLECTION_NAME)

    # Filtrelenen alanlar için keyword index (filtreleme için zorunlu)
    for field in ("ticker", "source_file"):
        try:
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD,
            )
        except Exception as e:  # index zaten varsa Qdrant hata döndürebilir
            logger.debug("Payload index (%s) atlandı: %s", field, e)
    logger.info("Payload index'leri hazır (ticker, source_file).")


def delete_existing_chunks(client: QdrantClient, ticker: str, source_file: str) -> None:
    """
    Aynı dosya yeniden yüklendiğinde eski chunk'ları temizler.
    Yeni sürüm daha az chunk üretirse artık kalıntı kalmaz.
    """
    try:
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(key="ticker", match=MatchValue(value=ticker)),
                        FieldCondition(key="source_file", match=MatchValue(value=source_file)),
                    ]
                )
            ),
        )
        logger.info("Önceki chunk'lar temizlendi: %s / %s", ticker, source_file)
    except Exception as e:
        logger.warning("Eski chunk temizleme başarısız (%s / %s): %s", ticker, source_file, e)


def embed_chunks(chunks: list[Chunk]) -> list[list[float]]:
    """Chunk'ları yerel multilingual model ile embed et. İnternet/API gerekmez."""
    model = get_model()
    texts = [c.text for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    return embeddings.tolist()


def upload_to_qdrant(client: QdrantClient, chunks: list[Chunk], embeddings: list[list[float]]):
    """Chunk'ları ve embedding'leri Qdrant'a yükle."""
    points = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        points.append(PointStruct(
            id=_point_id(chunk.ticker, chunk.source_file, idx),
            vector=embedding,
            payload={
                "text": chunk.text,
                "ticker": chunk.ticker,
                "page": chunk.page,
                "section": chunk.section,
                "source_file": chunk.source_file,
                "chunk_index": idx,
            }
        ))

    # 100'lük batch'ler halinde yükle
    batch_size = 100
    for i in range(0, len(points), batch_size):
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points[i:i + batch_size]
        )
        logger.info("Yüklendi: %d/%d", min(i + batch_size, len(points)), len(points))


def build_index(ticker: str, pdf_path: Path):
    ticker = ticker.upper()
    logger.info("--- %s index oluşturuluyor ---", ticker)

    # 1. PDF'i chunk'la
    chunks = chunk_pdf(pdf_path, ticker)
    if not chunks:
        logger.warning("%s: PDF'den chunk çıkarılamadı, index atlandı.", ticker)
        return

    # 2. Embed et
    logger.info("Embedding üretiliyor (%d chunk)...", len(chunks))
    embeddings = embed_chunks(chunks)

    # 3. Qdrant'a yükle (önce aynı dosyanın eski chunk'larını temizle)
    logger.info("Qdrant'a yükleniyor...")
    client = get_qdrant_client()
    ensure_collection(client)
    delete_existing_chunks(client, ticker, pdf_path.name)
    upload_to_qdrant(client, chunks, embeddings)

    logger.info("Tamamlandı. %d chunk Qdrant'a yazıldı.", len(chunks))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True, help="Örn: THYAO")
    parser.add_argument("--pdf", required=True, help="PDF dosya yolu")
    args = parser.parse_args()

    build_index(ticker=args.ticker, pdf_path=Path(args.pdf))
