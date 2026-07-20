"""
BIST finansal veri çekme ve SQLite'a yazma.

Kullanım:
    python -m src.ingestion.bist_finance_client --ticker THYAO
"""

import sqlite3
import argparse
from pathlib import Path

import yfinance as yf
import pandas as pd

DB_PATH = Path("data/bist_financials.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS income_statement (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker          TEXT NOT NULL,
            period_date     TEXT NOT NULL,
            revenue         REAL,
            gross_profit    REAL,
            ebitda          REAL,
            net_income      REAL,
            UNIQUE(ticker, period_date)
        );

        CREATE TABLE IF NOT EXISTS balance_sheet (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker          TEXT NOT NULL,
            period_date     TEXT NOT NULL,
            total_assets    REAL,
            total_debt      REAL,
            total_equity    REAL,
            cash            REAL,
            UNIQUE(ticker, period_date)
        );

        CREATE TABLE IF NOT EXISTS cash_flow (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker          TEXT NOT NULL,
            period_date     TEXT NOT NULL,
            operating_cf    REAL,
            investing_cf    REAL,
            financing_cf    REAL,
            free_cf         REAL,
            UNIQUE(ticker, period_date)
        );

        CREATE TABLE IF NOT EXISTS ratios (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker          TEXT NOT NULL,
            period_date     TEXT NOT NULL,
            pe_ratio        REAL,
            pb_ratio        REAL,
            net_margin      REAL,
            roe             REAL,
            roa             REAL,
            debt_to_equity  REAL,
            market_cap      REAL,
            current_price   REAL,
            UNIQUE(ticker, period_date)
        );

        CREATE TABLE IF NOT EXISTS dividends (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker      TEXT NOT NULL,
            ex_date     TEXT NOT NULL,
            amount      REAL,
            UNIQUE(ticker, ex_date)
        );

        CREATE INDEX IF NOT EXISTS idx_income_ticker ON income_statement(ticker);
        CREATE INDEX IF NOT EXISTS idx_balance_ticker ON balance_sheet(ticker);
        CREATE INDEX IF NOT EXISTS idx_cf_ticker ON cash_flow(ticker);
        CREATE INDEX IF NOT EXISTS idx_ratios_ticker ON ratios(ticker);
        CREATE INDEX IF NOT EXISTS idx_div_ticker ON dividends(ticker);
    """)
    conn.commit()


def _safe(val) -> float | None:
    """pandas NaN veya None değerlerini None'a çevir."""
    if val is None:
        return None
    try:
        f = float(val)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


def fetch_and_store(ticker: str) -> None:
    symbol = f"{ticker}.IS"
    print(f"yfinance'den çekiliyor: {symbol}")
    yf_ticker = yf.Ticker(symbol)

    conn = get_connection()
    create_tables(conn)

    # --- Gelir tablosu ---
    try:
        inc = yf_ticker.income_stmt
        if inc is not None and not inc.empty:
            def _get(df, row, col):
                return _safe(df.loc[row, col]) if row in df.index else None

            rows = 0
            for col in inc.columns:
                date_str = str(col.date()) if hasattr(col, "date") else str(col)[:10]
                conn.execute(
                    """INSERT OR REPLACE INTO income_statement
                       (ticker, period_date, revenue, gross_profit, ebitda, net_income)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        ticker,
                        date_str,
                        _get(inc, "Total Revenue", col),
                        _get(inc, "Gross Profit", col),
                        _get(inc, "EBITDA", col),
                        _get(inc, "Net Income", col),
                    ),
                )
                rows += 1
            conn.commit()
            print(f"  Gelir tablosu: {rows} dönem kaydedildi")
    except Exception as e:
        print(f"  Gelir tablosu hatası: {e}")

    # --- Bilanço ---
    try:
        bal = yf_ticker.balance_sheet
        if bal is not None and not bal.empty:
            def _getb(row, col):
                return _safe(bal.loc[row, col]) if row in bal.index else None

            rows = 0
            for col in bal.columns:
                date_str = str(col.date()) if hasattr(col, "date") else str(col)[:10]
                conn.execute(
                    """INSERT OR REPLACE INTO balance_sheet
                       (ticker, period_date, total_assets, total_debt, total_equity, cash)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        ticker,
                        date_str,
                        _getb("Total Assets", col),
                        _getb("Total Debt", col),
                        _getb("Stockholders Equity", col),
                        _getb("Cash And Cash Equivalents", col),
                    ),
                )
                rows += 1
            conn.commit()
            print(f"  Bilanço: {rows} dönem kaydedildi")
    except Exception as e:
        print(f"  Bilanço hatası: {e}")

    # --- Nakit akış ---
    try:
        cf = yf_ticker.cash_flow
        if cf is not None and not cf.empty:
            def _getcf(row, col):
                return _safe(cf.loc[row, col]) if row in cf.index else None

            rows = 0
            for col in cf.columns:
                date_str = str(col.date()) if hasattr(col, "date") else str(col)[:10]
                conn.execute(
                    """INSERT OR REPLACE INTO cash_flow
                       (ticker, period_date, operating_cf, investing_cf, financing_cf, free_cf)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        ticker,
                        date_str,
                        _getcf("Operating Cash Flow", col),
                        _getcf("Investing Cash Flow", col),
                        _getcf("Financing Cash Flow", col),
                        _getcf("Free Cash Flow", col),
                    ),
                )
                rows += 1
            conn.commit()
            print(f"  Nakit akış: {rows} dönem kaydedildi")
    except Exception as e:
        print(f"  Nakit akış hatası: {e}")

    # --- Oranlar: her dönem için net marj + anlık bilgiler ---
    try:
        info = yf_ticker.info
        today = pd.Timestamp.today().strftime("%Y-%m-%d")
        inc = yf_ticker.income_stmt

        # Her gelir tablosu dönemi için net marj hesapla
        if inc is not None and not inc.empty:
            for col in inc.columns:
                date_str = str(col.date()) if hasattr(col, "date") else str(col)[:10]
                ni = _safe(inc.loc["Net Income", col]) if "Net Income" in inc.index else None
                rev = _safe(inc.loc["Total Revenue", col]) if "Total Revenue" in inc.index else None
                net_margin = (ni / rev) * 100 if (ni and rev and rev != 0) else None
                conn.execute(
                    """INSERT OR REPLACE INTO ratios
                       (ticker, period_date, net_margin)
                       VALUES (?, ?, ?)""",
                    (ticker, date_str, net_margin),
                )
            conn.commit()

        # Anlık bilgileri bugünün tarihiyle ayrıca sakla
        conn.execute(
            """INSERT OR REPLACE INTO ratios
               (ticker, period_date, pe_ratio, pb_ratio, net_margin,
                roe, roa, debt_to_equity, market_cap, current_price)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                ticker,
                today,
                _safe(info.get("trailingPE")),
                _safe(info.get("priceToBook")),
                None,  # anlık satırda net_marj yok, dönemsel satırlarda var
                _safe(info.get("returnOnEquity")),
                _safe(info.get("returnOnAssets")),
                _safe(info.get("debtToEquity")),
                _safe(info.get("marketCap")),
                _safe(info.get("currentPrice")),
            ),
        )
        conn.commit()
        print(f"  Oranlar: dönemsel net marjlar + anlık veriler kaydedildi (fiyat: {info.get('currentPrice')} TRY)")
    except Exception as e:
        print(f"  Oranlar hatası: {e}")

    # --- Temettü ---
    try:
        divs = yf_ticker.dividends
        if divs is not None and not divs.empty:
            rows = 0
            for date, amount in divs.items():
                date_str = str(date.date()) if hasattr(date, "date") else str(date)[:10]
                conn.execute(
                    """INSERT OR REPLACE INTO dividends (ticker, ex_date, amount)
                       VALUES (?, ?, ?)""",
                    (ticker, date_str, _safe(amount)),
                )
                rows += 1
            conn.commit()
            print(f"  Temettü: {rows} ödeme kaydedildi")
    except Exception as e:
        print(f"  Temettü hatası: {e}")

    conn.close()
    print(f"\nTamamlandı. Veritabanı: {DB_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="THYAO")
    args = parser.parse_args()
    fetch_and_store(args.ticker)
