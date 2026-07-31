"""
Kaynak (citation) listesi testleri.

Kullanıcıya "bu cevap hangi dosyanın hangi sayfasından geldi" bilgisini
gösterebilmek için agent'ın döndürdüğü kaynak kayıtlarının doğru
şekillendiğini doğrular.
"""

import sqlite3

import pytest

from src.agent.synthesizer_node import (
    MAX_SOURCES, SNIPPET_LENGTH, _to_source, build_source_list,
)


def test_vector_source_carries_file_page_and_section():
    item = {
        "text": "THY 2025 yılında yolcu sayısını artırdı.",
        "ticker": "THYAO",
        "page": 23,
        "section": "Finansal Durum",
        "source_file": "THYAO_faaliyet_2026.pdf",
        "score": 0.8712,
        "source_type": "vector",
        "citation": "KAP — THYAO Faaliyet Raporu, s.23 (Finansal Durum)",
    }

    source = _to_source(item)

    assert source["type"] == "vector"
    assert source["source_file"] == "THYAO_faaliyet_2026.pdf"
    assert source["pages"] == [23]
    assert source["section"] == "Finansal Durum"
    assert source["score"] == 0.8712
    assert "yolcu" in source["snippet"]


def test_pdf_table_source_carries_multiple_pages():
    item = {
        "text": "[Sayfa 12 — rapor.pdf]\nGelir | 100",
        "ticker": "TUPRS",
        "source_type": "pdf",
        "source_file": "rapor.pdf",
        "pages": [12, 13],
        "score": 1.0,
        "citation": "PDF — TUPRS rapor.pdf (s.12, s.13)",
    }

    source = _to_source(item)

    assert source["type"] == "pdf"
    assert source["pages"] == [12, 13]
    assert source["source_file"] == "rapor.pdf"


def test_sql_source_carries_tables_and_period():
    item = {
        "text": "period_date=2024-12-31 | net_margin=12.08",
        "ticker": "THYAO",
        "source_type": "sql",
        "tables": ["income_statement", "ratios"],
        "period_range": "2022-12-31 – 2024-12-31",
        "score": 1.0,
        "citation": "yfinance — THYAO income_statement, ratios (2022-12-31 – 2024-12-31)",
    }

    source = _to_source(item)

    assert source["type"] == "sql"
    assert source["tables"] == ["income_statement", "ratios"]
    assert source["period_range"] == "2022-12-31 – 2024-12-31"


def test_news_source_carries_title_and_link():
    item = {
        "text": "THY yolcu rekoru\nDetay...",
        "ticker": "THYAO",
        "source_type": "news",
        "title": "THY yolcu rekoru",
        "link": "https://example.com/haber",
        "published_at": "2026-07-24 10:30:00",
        "score": 0.9,
        "citation": "Haber — Bloomberg HT: THY yolcu rekoru (2026-07-24)",
    }

    source = _to_source(item)

    assert source["type"] == "news"
    assert source["title"] == "THY yolcu rekoru"
    assert source["link"] == "https://example.com/haber"
    assert source["published_at"].startswith("2026-07-24")


def test_missing_source_type_defaults_to_vector():
    source = _to_source({"text": "x", "citation": "c"})
    assert source["type"] == "vector"


def test_snippet_is_truncated_with_ellipsis():
    long_text = "a" * (SNIPPET_LENGTH + 100)
    source = _to_source({"text": long_text, "source_type": "vector"})

    assert len(source["snippet"]) == SNIPPET_LENGTH + 1
    assert source["snippet"].endswith("…")


def test_source_list_is_capped_and_sorted_by_score():
    retrieved = [
        {"text": f"chunk {i}", "score": i / 100, "source_type": "vector", "page": i}
        for i in range(30)
    ]

    sources = build_source_list(retrieved)

    assert len(sources) == MAX_SOURCES
    scores = [s["score"] for s in sources]
    assert scores == sorted(scores, reverse=True)
    # En yüksek skorlu chunk (29) listede olmalı
    assert sources[0]["pages"] == [29]


def test_empty_retrieved_gives_empty_source_list():
    assert build_source_list([]) == []


def test_sql_retriever_reports_pdf_pages(tmp_path, monkeypatch):
    """pdf_tables sorgusu, hangi sayfalardan geldiğini kaynak kaydına yazmalı."""
    from src.retrievers import sql_retriever

    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE pdf_tables (ticker TEXT, source_file TEXT, page INTEGER,"
        " table_index INTEGER, table_text TEXT, uploaded_at TEXT)"
    )
    conn.executemany(
        "INSERT INTO pdf_tables VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("THYAO", "rapor.pdf", 12, 0, "Gelir | 100", "2026-07-30"),
            ("THYAO", "rapor.pdf", 13, 0, "Gider | 40", "2026-07-30"),
        ],
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(sql_retriever, "DB_PATH", db)
    monkeypatch.setattr(
        sql_retriever,
        "_generate_sql",
        lambda question, ticker: "SELECT * FROM pdf_tables WHERE ticker = 'THYAO' LIMIT 10",
    )

    results = sql_retriever.search("gelir tablosu", "THYAO")

    assert len(results) == 1
    assert results[0]["source_type"] == "pdf"
    assert results[0]["pages"] == [12, 13]
    assert results[0]["source_file"] == "rapor.pdf"
    assert "s.12, s.13" in results[0]["citation"]

    source = _to_source(results[0])
    assert source["pages"] == [12, 13]


def test_sql_retriever_reports_tables_for_financial_query(tmp_path, monkeypatch):
    from src.retrievers import sql_retriever

    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE ratios (ticker TEXT, period_date TEXT, net_margin REAL)")
    conn.executemany(
        "INSERT INTO ratios VALUES (?, ?, ?)",
        [("THYAO", "2024-12-31", 12.08), ("THYAO", "2023-12-31", 15.11)],
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(sql_retriever, "DB_PATH", db)
    monkeypatch.setattr(
        sql_retriever,
        "_generate_sql",
        lambda question, ticker: "SELECT * FROM ratios WHERE ticker = 'THYAO' LIMIT 10",
    )

    results = sql_retriever.search("net marj", "THYAO")

    assert results[0]["source_type"] == "sql"
    assert "ratios" in results[0]["tables"]
    assert results[0]["period_range"] is not None
