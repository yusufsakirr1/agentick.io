"""
News Retriever — RSS haberlerini arar, unified format'ta döndürür.

Kullanım:
    from src.retrievers.news_retriever import search
    results = search("THYAO hakkında son haberler", ticker="THYAO")
"""

from src.ingestion.news_client import fetch_news_if_stale, cleanup_old_news, search_news


def _score_result(article: dict, query: str, ticker: str) -> float:
    """Basit keyword overlap skorlaması."""
    score = 0.5  # taban skor
    query_lower = query.lower()
    keywords = query_lower.split()

    title_lower = (article.get("title") or "").lower()
    summary_lower = (article.get("summary") or "").lower()

    for kw in keywords:
        if kw in title_lower:
            score += 0.3
        if kw in summary_lower:
            score += 0.1

    # Ticker eşleşmesi varsa bonus
    tickers = article.get("tickers") or ""
    if ticker and ticker in tickers:
        score += 0.1

    # Tarih bilgisi varsa bonus
    if article.get("published_at"):
        score += 0.1

    return min(score, 1.0)


def search(query: str, ticker: str = "THYAO", top_k: int = 5) -> list[dict]:
    """
    Haber retriever — lazy fetch + keyword arama.
    Diğer retriever'larla aynı çıktı formatını döndürür.
    """
    # 1. Cache bayatsa RSS'ten çek
    new_count = fetch_news_if_stale()
    if new_count:
        print(f"  {new_count} yeni haber çekildi.")

    # 2. Eski haberleri temizle
    cleanup_old_news()

    # 3. SQLite'tan ara — önce ticker filtreli, sonuç yoksa genel arama
    articles = search_news(ticker=ticker, query=query, top_k=top_k)
    if not articles and ticker:
        articles = search_news(ticker=None, query=query, top_k=top_k)

    if not articles:
        return []

    # 4. Unified format'a çevir
    results = []
    for article in articles:
        source = article.get("source", "Bilinmeyen")
        title = article.get("title", "")
        published = article.get("published_at", "")
        date_str = published[:10] if published else "tarih bilinmiyor"
        link = article.get("link", "")
        summary = article.get("summary", "")

        text = f"{title}"
        if summary:
            text += f"\n{summary}"

        citation = f"Haber — {source}: {title} ({date_str})"

        results.append({
            "text": text,
            "ticker": ticker,
            "citation": citation,
            "score": _score_result(article, query, ticker),
            "source_type": "news",
            "link": link,
        })

    # Skora göre sırala
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    print("News retriever testi:")
    results = search("son haberler", ticker="THYAO", top_k=5)
    if not results:
        print("  Sonuç bulunamadı.")
    for r in results:
        print(f"  [{r['score']:.2f}] {r['citation']}")
        print(f"         {r['text'][:100]}...")
        print()
