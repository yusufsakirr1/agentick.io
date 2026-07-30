"""
POST /api/upload — PDF yükle ve indexle.
"""

import logging
import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, BackgroundTasks, status

from backend.constants import validate_ticker
from backend.rate_limit import enforce_rate_limit
from backend.services.pdf_pipeline import process_pdf

logger = logging.getLogger(__name__)

router = APIRouter()

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Dosya adı güvenlik filtresi: harf (Türkçe dahil), rakam, boşluk, . - _ ( )
SAFE_FILENAME_RE = re.compile(r"^[\w\-. ()]+$")


def _safe_filename(raw_name: str | None) -> str:
    """
    Dosya adını güvenli hale getirir:
      - dizin bileşenlerini atar (path traversal önleme)
      - '..' gibi tehlikeli adları reddeder
      - sadece PDF uzantısına izin verir
    """
    if not raw_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dosya adı boş olamaz.")

    # Hem POSIX hem Windows ayırıcılarını kırp, sadece taban adı al
    name = Path(raw_name.replace("\\", "/")).name.strip()

    if not name or name in {".", ".."} or ".." in name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dosya adı geçersiz.")
    if not name.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sadece PDF dosyaları kabul edilir.")
    if not SAFE_FILENAME_RE.match(name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dosya adı geçersiz karakter içeriyor.")
    if len(name) > 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dosya adı çok uzun.")

    return name


async def _read_and_store(file: UploadFile, ticker: str) -> Path:
    """Dosyayı boyut kontrolüyle okuyup data/raw altına yazar."""
    filename = _safe_filename(file.filename)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Dosya boyutu 50 MB'ı aşamaz.",
        )
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dosya boş.")
    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dosya geçerli bir PDF değil.")

    save_path = RAW_DIR / f"{ticker}_{filename}"
    save_path.write_bytes(content)
    return save_path


@router.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    ticker: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(enforce_rate_limit),
):
    ticker = validate_ticker(ticker)
    save_path = await _read_and_store(file, ticker)

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
    current_user: dict = Depends(enforce_rate_limit),
):
    """Sonucu bekleyerek yükle (frontend kullanır)."""
    ticker = validate_ticker(ticker)
    save_path = await _read_and_store(file, ticker)

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
