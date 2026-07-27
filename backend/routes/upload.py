"""
POST /api/upload — PDF yükle ve indexle.
"""

import logging
import re
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, BackgroundTasks, status

from backend.auth import get_current_user

from backend.services.pdf_pipeline import process_pdf

logger = logging.getLogger(__name__)

router = APIRouter()

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Geçerli BIST-30 ticker'ları
VALID_TICKERS = {
    "AKBNK", "AKSEN", "ARCLK", "ASELS", "BIMAS",
    "EKGYO", "ENKAI", "EREGL", "FROTO", "GARAN",
    "GUBRF", "HALKB", "ISCTR", "KCHOL", "KONTR",
    "KOZAL", "KRDMD", "ODAS",  "PETKM", "PGSUS",
    "SAHOL", "SASA",  "SISE",  "TAVHL", "TCELL",
    "THYAO", "TOASO", "TUPRS", "VAKBN", "YKBNK",
}

# Dosya adı güvenlik filtresi
SAFE_FILENAME_RE = re.compile(r"^[a-zA-Z0-9_\-\.]+$")


def _validate_ticker(ticker: str) -> str:
    """Ticker'ı doğrula ve normalize et."""
    ticker = ticker.upper().strip()
    if not ticker:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticker boş olamaz.")
    if ticker not in VALID_TICKERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Geçersiz ticker: {ticker}. Desteklenen: BIST-30.")
    return ticker


def _validate_file(file: UploadFile) -> None:
    """Dosya adı ve uzantısını doğrula."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sadece PDF dosyaları kabul edilir.")
    if not SAFE_FILENAME_RE.match(file.filename):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dosya adı geçersiz karakter içeriyor.")


@router.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    ticker: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    ticker = _validate_ticker(ticker)
    _validate_file(file)

    # Dosya boyut kontrolü
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Dosya boyutu 50 MB'ı aşamaz.")

    save_path = RAW_DIR / f"{ticker}_{file.filename}"
    with open(save_path, "wb") as f:
        f.write(content)

    # Pipeline'ı arka planda çalıştır
    background_tasks.add_task(_run_pipeline, save_path, ticker)

    return {
        "status": "processing",
        "message": f"{ticker} için PDF alındı, indexleme başladı.",
        "filename": save_path.name,
    }


@router.post("/upload/sync")
async def upload_pdf_sync(
    ticker: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Sonucu bekleyerek yükle (frontend kullanır)."""
    ticker = _validate_ticker(ticker)
    _validate_file(file)

    # Dosya boyut kontrolü
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Dosya boyutu 50 MB'ı aşamaz.")

    save_path = RAW_DIR / f"{ticker}_{file.filename}"
    with open(save_path, "wb") as f:
        f.write(content)

    result = await process_pdf(save_path, ticker)
    return {
        "status": "completed",
        "ticker": ticker,
        "filename": save_path.name,
        **result,
    }


async def _run_pipeline(pdf_path: Path, ticker: str):
    try:
        await process_pdf(pdf_path, ticker)
    except Exception as e:
        logger.error("Pipeline hatası (%s): %s", ticker, e)
