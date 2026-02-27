from __future__ import annotations

from typing import List


def extract_text_pdfplumber(pdf_path: str, max_pages: int | None = None) -> str:
    import pdfplumber

    lines: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        n = min(total, max_pages) if max_pages else total
        for i in range(n):
            page = pdf.pages[i]
            text = page.extract_text() or ""
            if text:
                lines.append(text)
    return "\n".join(lines)


def extract_text_pypdf(pdf_path: str, max_pages: int | None = None) -> str:
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    total = len(reader.pages)
    n = min(total, max_pages) if max_pages else total
    out: List[str] = []
    for i in range(n):
        out.append(reader.pages[i].extract_text() or "")
    return "\n".join(out)


def extract_text(pdf_path: str, max_pages: int | None = 20) -> str:
    """
    Best-effort text extraction. For scanned PDFs (images), this will likely
    return empty text; OCR would be needed (not included yet).
    """
    try:
        text = extract_text_pdfplumber(pdf_path, max_pages=max_pages)
        if text and text.strip():
            return text
    except Exception:
        pass

    return extract_text_pypdf(pdf_path, max_pages=max_pages)

