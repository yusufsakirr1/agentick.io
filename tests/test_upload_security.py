"""
Dosya adı güvenlik testleri (path traversal, uzantı, karakter seti).
"""

import pytest
from fastapi import HTTPException

from backend.routes.upload import _safe_filename


def test_accepts_plain_name():
    assert _safe_filename("THYAO_faaliyet_2026.pdf") == "THYAO_faaliyet_2026.pdf"


def test_accepts_spaces_and_turkish_characters():
    name = "TUPRS Entegre Faaliyet Raporu (2025).pdf"
    assert _safe_filename(name) == name
    assert _safe_filename("Şişecam Yıllık Rapor.pdf") == "Şişecam Yıllık Rapor.pdf"


def test_strips_directory_components():
    assert _safe_filename("/etc/passwd/rapor.pdf") == "rapor.pdf"
    assert _safe_filename("C:\\Users\\x\\rapor.pdf") == "rapor.pdf"


@pytest.mark.parametrize("name", [
    "../../etc/passwd.pdf",
    "..\\..\\windows\\system32\\x.pdf",
    "....//....//gizli.pdf",
])
def test_traversal_is_neutralised(name):
    """Dizin bileşenleri atılır; sonuç data/raw dışına çıkamaz."""
    safe = _safe_filename(name)
    assert "/" not in safe and "\\" not in safe
    assert ".." not in safe
    assert safe.endswith(".pdf")


@pytest.mark.parametrize("name", ["..", "../..", "rapor..pdf"])
def test_rejects_dotdot_names(name):
    with pytest.raises(HTTPException) as exc:
        _safe_filename(name)
    assert exc.value.status_code == 400


@pytest.mark.parametrize("name", ["notes.txt", "archive.zip", "rapor", "rapor.pdf.exe"])
def test_rejects_non_pdf(name):
    with pytest.raises(HTTPException) as exc:
        _safe_filename(name)
    assert exc.value.status_code == 400


@pytest.mark.parametrize("name", ["", None, "   "])
def test_rejects_empty(name):
    with pytest.raises(HTTPException):
        _safe_filename(name)


def test_rejects_shell_characters():
    with pytest.raises(HTTPException):
        _safe_filename("rapor;rm -rf.pdf")


def test_rejects_too_long_name():
    with pytest.raises(HTTPException):
        _safe_filename("a" * 250 + ".pdf")
