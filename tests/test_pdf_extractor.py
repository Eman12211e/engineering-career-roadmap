import logging

import fitz
import pytest

from engine import pdf_extractor as pe
from engine.pdf_extractor import PDFExtractionError, pdf_to_clean_text, validate_text_input

SENTINEL = "ZQXSENTINEL7731UNIQUE"
BODY = "Mechanical engineer with CAD, SolidWorks and FEA experience. " * 3


def make_pdf(text=BODY, pages=1, encrypt=False):
    doc = fitz.open()
    for i in range(pages):
        doc.new_page().insert_text((72, 72), text if i == 0 else f"{text} {i}")
    kw = {"encryption": fitz.PDF_ENCRYPT_AES_256, "user_pw": "x", "owner_pw": "y"} if encrypt else {}
    data = doc.tobytes(**kw)
    doc.close()
    return data


def test_happy_path():
    assert "SolidWorks" in pdf_to_clean_text(make_pdf())


@pytest.mark.parametrize("data", [b"", b"not a pdf at all", make_pdf()[:100]])
def test_bad_inputs(data):
    with pytest.raises(PDFExtractionError) as e:
        pdf_to_clean_text(data)
    assert e.value.user_message


def test_encrypted():
    with pytest.raises(PDFExtractionError, match="password"):
        pdf_to_clean_text(make_pdf(encrypt=True))


def test_image_only_too_little_text():
    with pytest.raises(PDFExtractionError, match="little text"):
        pdf_to_clean_text(make_pdf(text="hi"))


def test_size_boundary(monkeypatch):
    data = make_pdf()
    monkeypatch.setattr(pe, "MAX_PDF_BYTES", len(data))
    assert pdf_to_clean_text(data)
    monkeypatch.setattr(pe, "MAX_PDF_BYTES", len(data) - 1)
    with pytest.raises(PDFExtractionError, match="larger"):
        pdf_to_clean_text(data)


def test_page_boundary():
    assert pdf_to_clean_text(make_pdf(pages=pe.MAX_PDF_PAGES))
    with pytest.raises(PDFExtractionError, match="pages"):
        pdf_to_clean_text(make_pdf(pages=pe.MAX_PDF_PAGES + 1))


def test_text_length_boundary(monkeypatch):
    n = len(pdf_to_clean_text(make_pdf()))
    monkeypatch.setattr(pe, "MAX_TEXT_CHARS", n)
    assert pdf_to_clean_text(make_pdf())
    monkeypatch.setattr(pe, "MAX_TEXT_CHARS", n - 1)
    with pytest.raises(PDFExtractionError, match="longer"):
        pdf_to_clean_text(make_pdf())


def test_validate_text_input(monkeypatch):
    assert validate_text_input("  hi  ", "resume") == "hi"
    with pytest.raises(ValueError, match="empty"):
        validate_text_input("   ", "resume")
    monkeypatch.setattr(pe, "MAX_TEXT_CHARS", 5)
    assert validate_text_input("12345", "resume") == "12345"
    with pytest.raises(ValueError) as e:
        validate_text_input(SENTINEL, "resume")
    assert SENTINEL not in str(e.value)


def _chain(exc):
    while exc is not None:
        yield exc
        exc = exc.__cause__ or (None if exc.__suppress_context__ else exc.__context__)


def test_sentinel_never_leaks(capsys, caplog, monkeypatch):
    caplog.set_level(logging.DEBUG)
    text = f"{SENTINEL} " + BODY
    cases = [
        (make_pdf(text), None),
        (make_pdf(text, pages=pe.MAX_PDF_PAGES + 1), None),
        (make_pdf(text, encrypt=True), None),
        (make_pdf(text), 10),  # text too long
        (make_pdf(text)[:150], None),  # corrupt
    ]
    for data, cap in cases:
        if cap:
            monkeypatch.setattr(pe, "MAX_TEXT_CHARS", cap)
        try:
            pdf_to_clean_text(data)
        except PDFExtractionError as e:
            assert SENTINEL not in "".join(str(x) + repr(x) for x in _chain(e))
    monkeypatch.setattr(pe, "MAX_TEXT_CHARS", 5)
    with pytest.raises(ValueError) as e:
        validate_text_input(SENTINEL * 2, "resume")
    assert SENTINEL not in repr(e.value)
    out = capsys.readouterr()
    assert SENTINEL not in out.out + out.err + caplog.text
