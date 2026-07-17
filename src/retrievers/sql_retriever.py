"""
SQL Retriever — Türkçe soruyu SQL'e çevirir, SQLite'tan sayısal veri çeker.

Kullanım:
    from src.retrievers.sql_retriever import search
    results = search("THYAO'nun son 3 yılda net marjı nasıl değişti?", ticker="THYAO")
"""

import os
import sqlite3
import json
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path("data/bist_financials.db")

# Veritabanı şeması — Claude'a ne sorulabileceğini göstermek için
DB_SCHEMA = """
Tablo: pdf_tables
  ticker TEXT        -- Hisse kodu (ör. THYAO)
  source_file TEXT   -- PDF dosya adı
  page INTEGER       -- Sayfa numarası
  table_index INTEGER-- Tablonun sayfadaki sırası (0'dan başlar)
  table_text TEXT    -- Tablo içeriği metin formatında (satır | sütun yapısında)
  uploaded_at TEXT   -- Yükleme tarihi (YYYY-MM-DD HH:MM:SS)

Tablo: income_statement
  ticker TEXT          -- Hisse kodu (ör. THYAO)
  period_date TEXT     -- Dönem tarihi (YYYY-MM-DD)
  revenue REAL         -- Toplam gelir (TL)
  gross_profit REAL    -- Brüt kâr (TL)
  ebitda REAL          -- FAVÖK (TL)
  net_income REAL      -- Net kâr (TL)

Tablo: balance_sheet
  ticker TEXT
  period_date TEXT
  total_assets REAL    -- Toplam varlıklar (TL)
  total_debt REAL      -- Toplam borç (TL)
  total_equity REAL    -- Özkaynaklar (TL)
  cash REAL            -- Nakit ve nakit benzerleri (TL)

Tablo: cash_flow
  ticker TEXT
  period_date TEXT
  operating_cf REAL    -- Operasyonel nakit akışı (TL)
  investing_cf REAL    -- Yatırım nakit akışı (TL)
  financing_cf REAL    -- Finansman nakit akışı (TL)
  free_cf REAL         -- Serbest nakit akışı (TL)

Tablo: ratios
  ticker TEXT
  period_date TEXT
  pe_ratio REAL        -- Fiyat/Kazanç oranı
  pb_ratio REAL        -- Piyasa Değeri/Defter Değeri
  net_margin REAL      -- Net kâr marjı (%)
  roe REAL             -- Özkaynak kârlılığı
  roa REAL             -- Varlık kârlılığı
  debt_to_equity REAL  -- Borç/Özkaynak oranı
  market_cap REAL      -- Piyasa değeri (TL)
  current_price REAL   -- Güncel fiyat (TRY)
"""

TEXT_TO_SQL_PROMPT = """Sen bir finansal veritabanı uzmanısın. Kullanıcının Türkçe sorusunu SQLite SQL sorgusuna çevir.

Veritabanı şeması:
{schema}

Kurallar:
- Sadece SELECT sorgusu yaz, başka bir şey yazma.
- Ticker değeri her zaman büyük harf (THYAO, TUPRS gibi).
- Tarih formatı YYYY-MM-DD.
- Sonucu en fazla 10 satırla sınırla (LIMIT 10).
- Sadece SQL döndür, açıklama ekleme.
- pdf_tables sorgularında OR koşullarını parantez içine al: WHERE ticker = 'X' AND (table_text LIKE '%a%' OR table_text LIKE '%b%').
- pdf_tables için her zaman ticker filtresi ekle.

Ticker: {ticker}
Soru: {question}

SQL:"""


def _generate_sql(question: str, ticker: str) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": TEXT_TO_SQL_PROMPT.format(
                schema=DB_SCHEMA,
                ticker=ticker,
                question=question,
            )
        }]
    )
    raw = response.content[0].text.strip()
    # Kod bloğu varsa temizle
    raw = re.sub(r"```sql\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw)
    return raw.strip()


def _run_sql(sql: str) -> list[dict]:
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql)
        rows = [dict(r) for r in cursor.fetchall()]
    except Exception as e:
        rows = [{"error": str(e), "sql": sql}]
    finally:
        conn.close()
    return rows


def _rows_to_text(rows: list[dict], ticker: str, sql: str = "") -> str:
    if not rows:
        return f"{ticker} için veri bulunamadı."
    if "error" in rows[0]:
        return f"SQL hatası: {rows[0]['error']}"

    # pdf_tables sonuçları için sadece tablo içeriğini göster
    if "pdf_tables" in sql and "table_text" in rows[0]:
        parts = []
        for row in rows:
            header = f"[Sayfa {row.get('page', '?')} — {row.get('source_file', '')}]"
            parts.append(f"{header}\n{row.get('table_text', '')}")
        return "\n\n".join(parts)

    # Standart finansal tablo çıktısı
    lines = []
    skip_cols = {"id", "ticker", "source_file", "table_index", "uploaded_at"}
    for row in rows:
        parts = [f"{k}={v}" for k, v in row.items() if v is not None and k not in skip_cols]
        lines.append("  " + " | ".join(parts))
    return "\n".join(lines)


def search(question: str, ticker: str = "THYAO", top_k: int = 5) -> list[dict]:
    """
    Türkçe soruyu SQL'e çevirir, SQLite'tan veri çeker.
    vector_retriever.search() ile aynı çıktı formatını döndürür.
    """
    if not DB_PATH.exists():
        return []

    sql = _generate_sql(question, ticker)
    print(f"  Üretilen SQL: {sql}")

    rows = _run_sql(sql)
    text = _rows_to_text(rows, ticker, sql)

    if not rows or "error" in (rows[0] if rows else {}):
        return []

    # Hangi tablolar sorgulandı?
    all_tables = ["income_statement", "balance_sheet", "cash_flow", "ratios", "pdf_tables"]
    tables = [t for t in all_tables if t in sql]
    source = ", ".join(tables) if tables else "finansal tablolar"

    # pdf_tables için kaynak dosyasını citation'a ekle
    if "pdf_tables" in sql:
        files = list({r.get("source_file", "") for r in rows if r.get("source_file")})
        file_str = files[0] if len(files) == 1 else ", ".join(files)
        citation = f"PDF — {ticker} {file_str}"
    else:
        # Tarih aralığını bul
        dates = [str(r.get("period_date", "")) for r in rows if r.get("period_date")]
        date_range = f"{dates[-1]} – {dates[0]}" if len(dates) > 1 else (dates[0] if dates else "")
        citation = f"yfinance — {ticker} {source} ({date_range})" if date_range else f"yfinance — {ticker} {source}"

    return [{
        "text": text,
        "ticker": ticker,
        "citation": citation,
        "score": 1.0,
        "source_type": "sql",
        "raw_rows": rows,
    }]
