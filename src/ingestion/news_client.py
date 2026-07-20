"""
News Client — RSS kaynaklarından haber çekip SQLite'a yazar.

Lazy fetch stratejisi: cache bayatsa çek, yoksa mevcut veriyi kullan.

Kullanım:
    from src.ingestion.news_client import fetch_news_if_stale, search_news, cleanup_old_news
"""

import sqlite3
import time
import re
from datetime import datetime, timedelta
from pathlib import Path

import feedparser

DB_PATH = Path("data/bist_financials.db")

CACHE_TTL_SECONDS = 3600  # 1 saat
RETENTION_DAYS = 7

RSS_SOURCES = [
    ("Bloomberg HT", "https://www.bloomberght.com/rss"),
]

# Ticker eşleştirme sözlüğü — kural tabanlı
KNOWN_TICKERS: dict[str, list[str]] = {
    "THYAO": ["thy", "türk hava yolları", "thyao", "türk hava"],
    "TUPRS": ["tüpraş", "tuprs", "tupras"],
    "GARAN": ["garanti", "garan", "garanti bankası"],
    "AKBNK": ["akbank", "akbnk"],
    "ISCTR": ["iş bankası", "isctr", "isbank"],
    "HALKB": ["halkbank", "halkb"],
    "VAKBN": ["vakıfbank", "vakbn", "vakifbank"],
    "YKBNK": ["yapı kredi", "ykbnk", "yapıkredi"],
    "KCHOL": ["koç holding", "kchol", "koç"],
    "SAHOL": ["sabancı", "sahol", "sabancı holding"],
    "EREGL": ["ereğli", "eregl", "erdemir"],
    "ASELS": ["aselsan", "asels"],
    "BIMAS": ["bim", "bimas", "bim mağazaları"],
    "TCELL": ["turkcell", "tcell"],
    "FROTO": ["ford otosan", "froto", "ford"],
    "TOASO": ["tofaş", "toaso", "tofas"],
    "SISE": ["şişecam", "sise", "şişe cam"],
    "PGSUS": ["pegasus", "pgsus"],
    "TAVHL": ["tav", "tavhl", "tav havalimanları"],
    "EKGYO": ["emlak konut", "ekgyo"],
    "ENKAI": ["enka", "enkai"],
    "ARCLK": ["arçelik", "arclk", "arclik"],
    "PETKM": ["petkim", "petkm"],
    "KOZAL": ["koza altın", "kozal"],
    "KONTR": ["kontrolmatik", "kontr"],
    "KRDMD": ["kardemir", "krdmd"],
    "GUBRF": ["gübre fabrikaları", "gubrf"],
    "ODAS": ["odaş", "odas"],
    "SASA": ["sasa polyester", "sasa"],
    "AKSEN": ["aksa enerji", "aksen"],
}


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            link TEXT UNIQUE NOT NULL,
            summary TEXT,
            published_at TEXT,
            fetched_at TEXT NOT NULL,
            tickers TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_news_fetched_at ON news_articles(fetched_at)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_news_tickers ON news_articles(tickers)
    """)
    conn.commit()


def _match_tickers(text: str) -> str:
    """Metin içindeki ticker eşleşmelerini bulur, virgülle ayrılmış döndürür."""
    text_lower = text.lower()
    matched = []
    for ticker, keywords in KNOWN_TICKERS.items():
        for kw in keywords:
            if kw in text_lower:
                matched.append(ticker)
                break
    return ",".join(sorted(set(matched)))


def _parse_date(entry) -> str | None:
    """feedparser entry'sinden tarih parse et."""
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if published:
        try:
            return datetime(*published[:6]).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    return None


def _is_stale(conn: sqlite3.Connection) -> bool:
    """Son fetch zamanına bakarak cache'in bayat olup olmadığını kontrol et."""
    row = conn.execute("SELECT MAX(fetched_at) FROM news_articles").fetchone()
    if not row or not row[0]:
        return True
    try:
        last_fetch = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        return (datetime.now() - last_fetch).total_seconds() > CACHE_TTL_SECONDS
    except ValueError:
        return True


def fetch_news_if_stale() -> int:
    """Cache bayatsa RSS'ten haber çeker, yeni eklenen haber sayısını döndürür."""
    conn = sqlite3.connect(DB_PATH)
    _ensure_table(conn)

    if not _is_stale(conn):
        conn.close()
        return 0

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inserted = 0

    for source_name, url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                summary = entry.get("summary", "").strip()
                # HTML etiketlerini temizle
                summary = re.sub(r"<[^>]+>", "", summary).strip()
                published_at = _parse_date(entry)
                tickers = _match_tickers(f"{title} {summary}")

                try:
                    conn.execute(
                        """INSERT INTO news_articles (source, title, link, summary, published_at, fetched_at, tickers)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (source_name, title, link, summary, published_at, now, tickers),
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    # link UNIQUE constraint — duplicate, atla
                    pass
        except Exception as e:
            print(f"  RSS fetch hatası ({source_name}): {e}")

    conn.commit()
    conn.close()
    return inserted


def cleanup_old_news() -> int:
    """RETENTION_DAYS'den eski haberleri siler, silinen sayıyı döndürür."""
    conn = sqlite3.connect(DB_PATH)
    _ensure_table(conn)
    cutoff = (datetime.now() - timedelta(days=RETENTION_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.execute("DELETE FROM news_articles WHERE fetched_at < ?", (cutoff,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def search_news(ticker: str | None = None, query: str = "", top_k: int = 5) -> list[dict]:
    """
    SQLite'tan keyword araması ile haber döndürür.
    ticker verilmişse o ticker'a ait haberler filtrelenir.
    query verilmişse başlık/özet'te aranır.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _ensure_table(conn)

    conditions = []
    params: list = []

    if ticker:
        conditions.append("tickers LIKE ?")
        params.append(f"%{ticker}%")

    if query:
        keywords = query.lower().split()
        kw_clauses = []
        for kw in keywords:
            kw_clauses.append("(LOWER(title) LIKE ? OR LOWER(summary) LIKE ?)")
            params.extend([f"%{kw}%", f"%{kw}%"])
        if kw_clauses:
            conditions.append("(" + " OR ".join(kw_clauses) + ")")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"""
        SELECT source, title, link, summary, published_at, tickers
        FROM news_articles
        {where}
        ORDER BY published_at DESC
        LIMIT ?
    """
    params.append(top_k)

    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    conn.close()
    return rows


if __name__ == "__main__":
    print("Haber çekiliyor...")
    count = fetch_news_if_stale()
    print(f"  {count} yeni haber eklendi.")

    print("Eski haberler temizleniyor...")
    deleted = cleanup_old_news()
    print(f"  {deleted} eski haber silindi.")

    print("\nTHYAO haberleri:")
    results = search_news(ticker="THYAO", top_k=3)
    for r in results:
        print(f"  [{r['published_at']}] {r['title']}")

    print("\nTüm haberler (son 5):")
    results = search_news(top_k=5)
    for r in results:
        print(f"  [{r['source']}] {r['title']} — tickers: {r['tickers']}")
