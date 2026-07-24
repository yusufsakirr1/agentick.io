"""
Paylaşılan metrik helper fonksiyonları.

compare.py ve portfolio.py tarafından kullanılır.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/bist_financials.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_latest_ratios(conn: sqlite3.Connection, ticker: str) -> dict:
    """En son tarihli ratios satırını çek (bugünün anlık verisi)."""
    row = conn.execute(
        "SELECT * FROM ratios WHERE ticker = ? ORDER BY period_date DESC LIMIT 1",
        (ticker,),
    ).fetchone()
    result = dict(row) if row else {}

    if not result.get("net_margin"):
        margin_row = conn.execute(
            "SELECT net_margin FROM ratios WHERE ticker = ? AND net_margin IS NOT NULL ORDER BY period_date DESC LIMIT 1",
            (ticker,),
        ).fetchone()
        if margin_row:
            result["net_margin"] = margin_row["net_margin"]

    return result


def fetch_latest_income(conn: sqlite3.Connection, ticker: str) -> dict:
    row = conn.execute(
        "SELECT * FROM income_statement WHERE ticker = ? ORDER BY period_date DESC LIMIT 1",
        (ticker,),
    ).fetchone()
    return dict(row) if row else {}


def fetch_latest_balance(conn: sqlite3.Connection, ticker: str) -> dict:
    row = conn.execute(
        "SELECT * FROM balance_sheet WHERE ticker = ? ORDER BY period_date DESC LIMIT 1",
        (ticker,),
    ).fetchone()
    return dict(row) if row else {}


def fetch_dividend_yield(conn: sqlite3.Connection, ticker: str, current_price: float | None) -> float | None:
    if not current_price:
        return None
    row = conn.execute(
        "SELECT SUM(amount) AS total FROM dividends WHERE ticker = ? AND ex_date >= date('now', '-1 year')",
        (ticker,),
    ).fetchone()
    total = row["total"] if row and row["total"] else 0
    if total and current_price > 0:
        return round((total / current_price) * 100, 2)
    return None


def fetch_dividends(conn: sqlite3.Connection, ticker: str) -> list[dict]:
    """Son 2 yıllık temettü verilerini döndür."""
    rows = conn.execute(
        "SELECT ticker, ex_date, amount FROM dividends WHERE ticker = ? AND ex_date >= date('now', '-2 year') ORDER BY ex_date DESC",
        (ticker,),
    ).fetchall()
    return [dict(r) for r in rows]


def build_ticker_metrics(conn: sqlite3.Connection, ticker: str) -> dict:
    ratios = fetch_latest_ratios(conn, ticker)
    income = fetch_latest_income(conn, ticker)
    balance = fetch_latest_balance(conn, ticker)
    current_price = ratios.get("current_price")
    dividend_yield = fetch_dividend_yield(conn, ticker, current_price)

    roe = ratios.get("roe")
    roa = ratios.get("roa")
    if roe is not None and abs(roe) < 1:
        roe = round(roe * 100, 2)
    if roa is not None and abs(roa) < 1:
        roa = round(roa * 100, 2)

    debt_to_equity = ratios.get("debt_to_equity")
    if debt_to_equity is None:
        total_debt = balance.get("total_debt")
        total_equity = balance.get("total_equity")
        if total_debt and total_equity and total_equity != 0:
            debt_to_equity = round(total_debt / total_equity, 2)

    ebitda = income.get("ebitda")
    sector = ratios.get("sector")

    return {
        "ticker": ticker,
        "current_price": current_price,
        "market_cap": ratios.get("market_cap"),
        "pe_ratio": ratios.get("pe_ratio"),
        "pb_ratio": ratios.get("pb_ratio"),
        "net_margin": ratios.get("net_margin"),
        "roe": roe,
        "roa": roa,
        "debt_to_equity": debt_to_equity,
        "dividend_yield": dividend_yield,
        "revenue": income.get("revenue"),
        "net_income": income.get("net_income"),
        "ebitda": ebitda,
        "total_assets": balance.get("total_assets"),
        "total_equity": balance.get("total_equity"),
        "total_debt": balance.get("total_debt"),
        "ratios_date": ratios.get("period_date"),
        "income_date": income.get("period_date"),
        "sector": sector,
    }
