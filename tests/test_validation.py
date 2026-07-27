"""
Input validation testleri.
"""

import pytest


def test_ask_empty_question_returns_400(client):
    response = client.post("/api/ask", json={
        "question": "",
        "ticker": "THYAO",
    })
    assert response.status_code == 400


def test_ask_missing_question_returns_422(client):
    response = client.post("/api/ask", json={
        "ticker": "THYAO",
    })
    assert response.status_code == 422


def test_fetch_data_empty_ticker_returns_400(client):
    response = client.post("/api/fetch-data", json={
        "ticker": "",
    })
    assert response.status_code == 400


def test_compare_metrics_single_ticker_returns_400(client):
    response = client.get("/api/compare/metrics?tickers=THYAO",
                          headers={"Authorization": "Bearer dev-token"})
    assert response.status_code == 400


def test_compare_metrics_too_many_tickers_returns_400(client):
    response = client.get("/api/compare/metrics?tickers=THYAO,TUPRS,GARAN,AKBNK,EREGL,ASELS",
                          headers={"Authorization": "Bearer dev-token"})
    assert response.status_code == 400


def test_portfolio_metrics_empty_holdings_returns_400(client):
    response = client.post("/api/portfolio/metrics", json={
        "holdings": [],
    })
    assert response.status_code == 400


def test_portfolio_ask_empty_question_returns_400(client):
    response = client.post("/api/portfolio/ask", json={
        "question": "",
        "tickers": ["THYAO"],
    })
    assert response.status_code == 400


def test_portfolio_ask_no_tickers_returns_400(client):
    response = client.post("/api/portfolio/ask", json={
        "question": "Portföyüm nasıl?",
        "tickers": [],
    })
    assert response.status_code == 400


def test_portfolio_news_no_tickers_returns_400(client):
    response = client.post("/api/portfolio/news", json={
        "tickers": [],
    })
    assert response.status_code == 400


def test_upload_invalid_ticker_returns_400(client):
    import io
    response = client.post(
        "/api/upload",
        data={"ticker": "INVALID"},
        files={"file": ("test.pdf", io.BytesIO(b"%PDF-test"), "application/pdf")},
    )
    assert response.status_code == 400
    assert "Geçersiz ticker" in response.json()["detail"]


def test_upload_non_pdf_returns_400(client):
    import io
    response = client.post(
        "/api/upload",
        data={"ticker": "THYAO"},
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400
