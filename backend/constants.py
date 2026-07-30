"""
Backend genelinde paylaşılan sabitler ve doğrulama helper'ları.

Ticker whitelist'i tek kaynaktan yönetilir — frontend'deki
`frontend/src/constants/tickers.ts` ile aynı listedir.
"""

from fastapi import HTTPException, status

# Desteklenen BIST-30 hisseleri (tek kaynak)
VALID_TICKERS: frozenset[str] = frozenset({
    "AKBNK", "AKSEN", "ARCLK", "ASELS", "BIMAS",
    "EKGYO", "ENKAI", "EREGL", "FROTO", "GARAN",
    "GUBRF", "HALKB", "ISCTR", "KCHOL", "KONTR",
    "KOZAL", "KRDMD", "ODAS",  "PETKM", "PGSUS",
    "SAHOL", "SASA",  "SISE",  "TAVHL", "TCELL",
    "THYAO", "TOASO", "TUPRS", "VAKBN", "YKBNK",
})


def validate_ticker(ticker: str) -> str:
    """Tek bir ticker'ı normalize edip whitelist'e karşı doğrular."""
    normalized = (ticker or "").upper().strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticker boş olamaz.",
        )
    if normalized not in VALID_TICKERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Geçersiz ticker: {normalized}. Desteklenen: BIST-30.",
        )
    return normalized


def validate_tickers(tickers: list[str], *, min_count: int = 1, max_count: int = 5) -> list[str]:
    """Ticker listesini normalize eder, tekrarları korur, whitelist'e karşı doğrular."""
    cleaned = [t for t in (tickers or []) if t and t.strip()]
    if len(cleaned) < min_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"En az {min_count} ticker gerekli.",
        )
    if len(cleaned) > max_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"En fazla {max_count} ticker desteklenir.",
        )
    return [validate_ticker(t) for t in cleaned]
