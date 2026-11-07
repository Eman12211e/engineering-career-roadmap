"""PDF text extraction and cleaning for resume parsing.

Extracts raw text from uploaded PDF resumes using PyMuPDF (fitz),
then cleans common PDF artifacts: broken lines, hyphenated words,
page numbers, headers/footers, and junk characters.
"""

import re
import fitz  # PyMuPDF

from config.settings import (
    MAX_PDF_BYTES,
    MAX_PDF_PAGES,
    MAX_TEXT_CHARS,
    MIN_EXTRACTED_CHARS,
)


class PDFExtractionError(Exception):
    """Raised for unusable PDFs. Messages never contain document content."""

    def __init__(self, user_message: str):
        super().__init__(user_message)
        self.user_message = user_message


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF's bytes, enforcing size and page limits."""
    if not pdf_bytes:
        raise PDFExtractionError("The uploaded file is empty.")
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise PDFExtractionError(
            f"The PDF is larger than {MAX_PDF_BYTES // (1024 * 1024)} MB. Please upload a smaller file."
        )
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        raise PDFExtractionError("That file could not be read as a PDF.") from None
    try:
        if doc.needs_pass or doc.is_encrypted:
            raise PDFExtractionError("The PDF is password-protected. Please upload an unlocked copy.")
        if doc.page_count > MAX_PDF_PAGES:
            raise PDFExtractionError(
                f"The PDF has more than {MAX_PDF_PAGES} pages. Please upload a shorter document."
            )
        try:
            return "\n".join(page.get_text() for page in doc)
        except Exception:
            raise PDFExtractionError("The PDF text could not be extracted.") from None
    finally:
        doc.close()


def clean_pdf_text(raw_text: str) -> str:
    """Clean common PDF extraction artifacts from resume text.

    Handles:
    - Hyphenated words split across lines (e.g., "Soft-\\nware" → "Software")
    - Page numbers and page indicators ("Page 1", "1/3", etc.)
    - Excessive blank lines
    - Leading/trailing whitespace per line
    - Common footer/watermark patterns
    """
    text = raw_text

    # Fix hyphenated words split across lines
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

    # Remove page numbers: "Page 1", "Page 2 of 5", "1/3", "- 1 -", etc.
    text = re.sub(r"(?i)\bpage\s+\d+(\s+of\s+\d+)?\b", "", text)
    text = re.sub(r"^\s*\d+\s*/\s*\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*-\s*\d+\s*-\s*$", "", text, flags=re.MULTILINE)

    # Remove standalone page numbers (a line that is just a number)
    text = re.sub(r"^\s*\d{1,3}\s*$", "", text, flags=re.MULTILINE)

    # Remove common confidential disclaimers
    text = re.sub(
        r"(?i)\b(confidential|do not distribute|private & confidential)\b.*$",
        "",
        text,
        flags=re.MULTILINE,
    )

    # Collapse multiple blank lines into one
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)

    return text.strip()


def validate_text_input(text: str, field: str) -> str:
    """Strip pasted text; reject empty or over-long input without echoing it."""
    text = (text or "").strip()
    if not text:
        raise ValueError(f"The {field} is empty.")
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(f"The {field} is longer than {MAX_TEXT_CHARS:,} characters.")
    return text


def pdf_to_clean_text(pdf_bytes: bytes) -> str:
    """Full pipeline: PDF bytes -> extracted text -> cleaned text.

    Raises PDFExtractionError (plain user_message, no content) on bad input.
    """
    text = clean_pdf_text(extract_text_from_pdf(pdf_bytes))
    if len(text) < MIN_EXTRACTED_CHARS:
        raise PDFExtractionError(
            "Very little text was found. The PDF may be a scanned image; paste the text instead."
        )
    if len(text) > MAX_TEXT_CHARS:
        raise PDFExtractionError(
            f"The PDF text is longer than {MAX_TEXT_CHARS:,} characters. Please upload a shorter document."
        )
    return text
