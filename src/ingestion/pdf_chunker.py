"""
Türkçe PDF dosyalarını semantic chunk'lara böler.

Kullanım:
    python -m src.ingestion.pdf_chunker data/raw/THYAO_xxxx.pdf
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass

import fitz  # pymupdf


CHUNK_SIZE = 600       # hedef token sayısı (yaklaşık kelime × 1.3)
CHUNK_OVERLAP = 80     # örtüşme (context sürekliliği için)

# KAP faaliyet raporlarında sık geçen bölüm başlıkları
SECTION_PATTERNS = [
    r"^(BÖLÜM|KISIM)\s+\d+",
    r"^\d+\.\s+[A-ZÇĞİÖŞÜ]",
    r"^(FİNANSAL DURUM|GELİR TABLOSU|NAKİT AKIŞ|ÖZ KAYNAKLAR)",
    r"^(YÖNETİM KURULU|DENETÇİ RAPORU|BAĞIMSIZ DENETİM)",
    r"^(RİSK|STRATEJİ|HEDEF|GENEL BİLGİ)",
]
SECTION_RE = re.compile("|".join(SECTION_PATTERNS), re.IGNORECASE)


@dataclass
class Chunk:
    text: str
    page: int
    section: str
    ticker: str
    source_file: str


def extract_text_by_page(pdf_path: Path) -> list[tuple[int, str]]:
    """PDF'den sayfa numarasıyla birlikte metin çıkar."""
    doc = fitz.open(str(pdf_path))
    pages = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        if text.strip():
            pages.append((page_num, text))
    doc.close()
    return pages


def detect_section(text: str) -> str:
    """Metnin hangi bölüme ait olduğunu tahmin et."""
    for line in text.splitlines()[:5]:
        line = line.strip()
        if SECTION_RE.match(line) and len(line) < 120:
            return line
    return "Genel"


def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Metni kelime bazında chunk'lara böler.
    Token sayısı yerine kelime sayısı kullanıyoruz (yaklaşık, hızlı).
    """
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) > 50:  # çok kısa chunk'ları atla
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def chunk_pdf(pdf_path: Path, ticker: str) -> list[Chunk]:
    """PDF'i chunk'lara böler ve metadata ekler."""
    pages = extract_text_by_page(pdf_path)
    print(f"{pdf_path.name}: {len(pages)} sayfa okundu")

    all_chunks: list[Chunk] = []
    current_section = "Giriş"

    for page_num, page_text in pages:
        # Bölüm başlığı var mı kontrol et
        detected = detect_section(page_text)
        if detected != "Genel":
            current_section = detected

        text_chunks = split_into_chunks(page_text)
        for chunk_text in text_chunks:
            all_chunks.append(Chunk(
                text=chunk_text,
                page=page_num,
                section=current_section,
                ticker=ticker,
                source_file=pdf_path.name,
            ))

    print(f"Toplam {len(all_chunks)} chunk oluşturuldu")
    return all_chunks


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python -m src.ingestion.pdf_chunker <pdf_path> [ticker]")
        sys.exit(1)

    pdf = Path(sys.argv[1])
    ticker = sys.argv[2] if len(sys.argv) > 2 else "BILINMIYOR"
    chunks = chunk_pdf(pdf, ticker)

    print(f"\nİlk chunk örneği:")
    print(f"  Sayfa: {chunks[0].page}")
    print(f"  Bölüm: {chunks[0].section}")
    print(f"  Metin: {chunks[0].text[:200]}...")
