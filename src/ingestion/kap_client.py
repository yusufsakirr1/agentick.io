"""
KAP.org.tr'dan şirket faaliyet raporlarını indirir.

KAP, API isteklerini engelliyor. Bu nedenle PDF'ler manuel olarak
indirilip data/raw/ klasörüne konulmalıdır.

Manuel indirme adımları:
    1. kap.org.tr adresine git
    2. Arama kutusuna şirket adını yaz (ör. "Türk Hava Yolları")
    3. Şirket sayfasına gir → "Finansal Raporlar" sekmesi
    4. En son "Yıllık Faaliyet Raporu" PDF'ini indir
    5. data/raw/THYAO_faaliyet_2024.pdf olarak kaydet

Kullanım (doğrulama için):
    python -m src.ingestion.kap_client
"""

from pathlib import Path

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def list_downloaded_pdfs() -> list[Path]:
    """data/raw/ klasöründeki PDF'leri listeler."""
    return list(RAW_DIR.glob("*.pdf"))


def validate_pdf(path: Path) -> bool:
    """Dosyanın geçerli bir PDF olduğunu kontrol eder."""
    if not path.exists():
        return False
    with open(path, "rb") as f:
        header = f.read(4)
    return header == b"%PDF"


if __name__ == "__main__":
    pdfs = list_downloaded_pdfs()

    if not pdfs:
        print("data/raw/ klasöründe PDF bulunamadı.")
        print()
        print("Manuel indirme adımları:")
        print("  1. https://www.kap.org.tr adresine git")
        print("  2. Arama kutusuna 'Türk Hava Yolları' yaz")
        print("  3. Şirket sayfası → Finansal Raporlar sekmesi")
        print("  4. En son Yıllık Faaliyet Raporu PDF'ini indir")
        print("  5. Dosyayı data/raw/THYAO_faaliyet_2024.pdf olarak kaydet")
    else:
        for pdf in pdfs:
            valid = validate_pdf(pdf)
            status = "geçerli PDF" if valid else "HATA: geçersiz dosya"
            size_kb = pdf.stat().st_size // 1024
            print(f"  {pdf.name} — {size_kb} KB — {status}")
        print(f"\nToplam {len(pdfs)} PDF hazır.")
