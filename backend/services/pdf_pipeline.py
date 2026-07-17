"""
PDF Pipeline — Yüklenen PDF'i işler:
  1. pdfplumber → tabloları çıkar → SQLite pdf_tables
  2. pymupdf + pdf_chunker → metni chunk'la → embed → Qdrant
  3. yfinance → finansal verileri güncelle → SQLite
"""

import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime

import pdfplumber

from src.ingestion.build_vector_index import build_index
from src.ingestion.bist_finance_client import fetch_and_store

DB_PATH = Path("data/bist_financials.db")


def _ensure_pdf_tables(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pdf_tables (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker      TEXT NOT NULL,
            source_file TEXT NOT NULL,
            page        INTEGER,
            table_index INTEGER,
            table_text  TEXT NOT NULL,
            uploaded_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_pdf_tables_ticker
        ON pdf_tables(ticker)
    """)
    conn.commit()


def _table_to_text(table: list[list]) -> str:
    """pdfplumber table listesini okunabilir metne çevirir."""
    lines = []
    for row in table:
        cleaned = [str(cell).strip() if cell is not None else "" for cell in row]
        lines.append(" | ".join(cleaned))
    return "\n".join(lines)


def _extract_and_store_tables(pdf_path: Path, ticker: str) -> int:
    """PDF'deki tabloları SQLite'a yaz. Kaç tablo bulunduğunu döndürür."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    _ensure_pdf_tables(conn)

    # Eski kayıtları temizle (aynı dosya tekrar yüklenirse)
    conn.execute(
        "DELETE FROM pdf_tables WHERE ticker = ? AND source_file = ?",
        (ticker.upper(), pdf_path.name),
    )
    conn.commit()

    total_tables = 0
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for t_idx, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue
                table_text = _table_to_text(table)
                if len(table_text.strip()) < 20:
                    continue
                conn.execute(
                    """INSERT INTO pdf_tables
                       (ticker, source_file, page, table_index, table_text, uploaded_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        ticker.upper(),
                        pdf_path.name,
                        page_num,
                        t_idx,
                        table_text,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )
                total_tables += 1

    conn.commit()
    conn.close()
    return total_tables


async def process_pdf(pdf_path: Path, ticker: str) -> dict:
    """
    PDF'i tam olarak işler:
    - Tabloları SQLite'a yazar
    - Metni embed edip Qdrant'a yükler
    - yfinance verilerini günceller

    Returns:
        {"tables": int, "chunks_indexed": bool, "yfinance_updated": bool}
    """
    ticker = ticker.upper()
    result = {}

    # 1. Tablo çıkarma → SQLite
    tables_count = await asyncio.to_thread(_extract_and_store_tables, pdf_path, ticker)
    result["tables"] = tables_count

    # 2. Metin chunklama + embed → Qdrant
    try:
        await asyncio.to_thread(build_index, ticker, pdf_path)
        result["chunks_indexed"] = True
    except Exception as e:
        result["chunks_indexed"] = False
        result["index_error"] = str(e)

    # 3. yfinance → SQLite (arka planda, hata olursa devam et)
    try:
        await asyncio.to_thread(fetch_and_store, ticker)
        result["yfinance_updated"] = True
    except Exception as e:
        result["yfinance_updated"] = False
        result["yfinance_error"] = str(e)

    return result
