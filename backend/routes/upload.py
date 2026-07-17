"""
POST /api/upload — PDF yükle ve indexle.
"""

import shutil
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, BackgroundTasks

from backend.services.pdf_pipeline import process_pdf

router = APIRouter()

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    ticker: str = Form(...),
    file: UploadFile = File(...),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları kabul edilir.")

    ticker = ticker.upper().strip()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker boş olamaz.")

    # Dosyayı kaydet
    save_path = RAW_DIR / f"{ticker}_{file.filename}"
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

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
):
    """Sonucu bekleyerek yükle (test için)."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları kabul edilir.")

    ticker = ticker.upper().strip()
    save_path = RAW_DIR / f"{ticker}_{file.filename}"
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

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
        print(f"[Pipeline hatası] {ticker}: {e}")
