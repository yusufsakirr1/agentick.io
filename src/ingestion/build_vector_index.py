"""
PDF chunk'larını embedding'e çevirip Qdrant'a yazar.

Kullanım:
    python -m src.ingestion.build_vector_index --ticker THYAO --pdf data/raw/THYAO_xxxx.pdf
"""

import logging
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from src.ingestion.pdf_chunker import chunk_pdf, Chunk

load_dotenv()

logger = logging.getLogger(__name__)

COLLECTION_NAME = "kap_filings"
VECTOR_SIZE = 768  # paraphrase-multilingual-mpnet-base-v2 boyutu
EMBED_MODEL = "paraphrase-multilingual-mpnet-base-v2"  # Türkçe destekli, ücretsiz

def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        url=os.environ.get("QDRANT_URL", ""),
        api_key=os.environ.get("QDRANT_API_KEY", ""),
    )


def ensure_collection(client: QdrantClient):
    """Collection yoksa oluştur, payload index'i ekle."""
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

    # ticker alanı için keyword index (filtreleme için zorunlu)
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="ticker",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    logger.info("ticker index hazır.")


def embed_chunks(chunks: list[Chunk]) -> list[list[float]]:
    """Chunk'ları yerel multilingual model ile embed et. İnternet/API gerekmez."""
    logger.info("Model yükleniyor: %s (ilk seferde ~500MB indirilir)", EMBED_MODEL)
    model = SentenceTransformer(EMBED_MODEL)
    texts = [c.text for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    return embeddings.tolist()


def upload_to_qdrant(client: QdrantClient, chunks: list[Chunk], embeddings: list[list[float]]):
    """Chunk'ları ve embedding'leri Qdrant'a yükle."""
    points = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        points.append(PointStruct(
            id=idx,
            vector=embedding,
            payload={
                "text": chunk.text,
                "ticker": chunk.ticker,
                "page": chunk.page,
                "section": chunk.section,
                "source_file": chunk.source_file,
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
    logger.info("--- %s index oluşturuluyor ---", ticker)

    # 1. PDF'i chunk'la
    chunks = chunk_pdf(pdf_path, ticker)

    # 2. Embed et
    logger.info("Embedding üretiliyor (%d chunk)...", len(chunks))
    embeddings = embed_chunks(chunks)

    # 3. Qdrant'a yükle
    logger.info("Qdrant'a yükleniyor...")
    client = get_qdrant_client()
    ensure_collection(client)
    upload_to_qdrant(client, chunks, embeddings)

    logger.info("Tamamlandı. %d chunk Qdrant'a yazıldı.", len(chunks))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True, help="Örn: THYAO")
    parser.add_argument("--pdf", required=True, help="PDF dosya yolu")
    args = parser.parse_args()

    build_index(ticker=args.ticker, pdf_path=Path(args.pdf))
