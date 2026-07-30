"""
SQL retriever güvenlik testleri.

LLM'in ürettiği SQL doğrudan çalıştırıldığı için sadece tek bir SELECT
kabul edilmelidir. Aksi halde PDF içeriği üzerinden prompt injection ile
veri silinebilir/değiştirilebilir.
"""

import pytest

from src.retrievers.sql_retriever import _validate_sql


SAFE_QUERIES = [
    "SELECT ticker, net_margin FROM ratios WHERE ticker = 'THYAO' LIMIT 10",
    "select * from dividends where ticker='TUPRS' order by ex_date desc limit 10",
    "SELECT ticker, net_margin FROM ratios WHERE ticker = 'THYAO' LIMIT 10;",
    "WITH son AS (SELECT * FROM ratios WHERE ticker='SASA') SELECT * FROM son LIMIT 5",
]

UNSAFE_QUERIES = [
    "DELETE FROM ratios",
    "DROP TABLE dividends",
    "UPDATE ratios SET current_price = 0 WHERE ticker = 'THYAO'",
    "INSERT INTO ratios (ticker) VALUES ('X')",
    "ALTER TABLE ratios ADD COLUMN evil TEXT",
    "SELECT 1; DROP TABLE ratios",
    "SELECT * FROM ratios; DELETE FROM dividends;",
    "PRAGMA table_info(ratios)",
    "ATTACH DATABASE '/tmp/evil.db' AS evil",
    "SELECT * FROM ratios -- yorum",
    "",
    "   ",
]


@pytest.mark.parametrize("sql", SAFE_QUERIES)
def test_safe_queries_pass(sql):
    assert _validate_sql(sql) is None


@pytest.mark.parametrize("sql", UNSAFE_QUERIES)
def test_unsafe_queries_rejected(sql):
    assert _validate_sql(sql) is not None


def test_rejected_sql_returns_error_row(tmp_path, monkeypatch):
    """Reddedilen sorgu veritabanına hiç gitmemeli, error satırı dönmeli."""
    import sqlite3
    from src.retrievers import sql_retriever

    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE ratios (ticker TEXT, current_price REAL)")
    conn.execute("INSERT INTO ratios VALUES ('THYAO', 100.0)")
    conn.commit()
    conn.close()

    monkeypatch.setattr(sql_retriever, "DB_PATH", db)

    rows = sql_retriever._run_sql("DELETE FROM ratios")
    assert "error" in rows[0]

    # Veri hâlâ yerinde
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM ratios").fetchone()[0] == 1
    conn.close()


def test_connection_is_read_only(tmp_path, monkeypatch):
    """Guard atlansa bile bağlantı salt-okunur olmalı."""
    import sqlite3
    from src.retrievers import sql_retriever

    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE ratios (ticker TEXT)")
    conn.commit()
    conn.close()

    monkeypatch.setattr(sql_retriever, "DB_PATH", db)
    monkeypatch.setattr(sql_retriever, "_validate_sql", lambda _sql: None)

    rows = sql_retriever._run_sql("INSERT INTO ratios VALUES ('X')")
    assert "error" in rows[0]
    assert "readonly" in rows[0]["error"].lower() or "read-only" in rows[0]["error"].lower()
