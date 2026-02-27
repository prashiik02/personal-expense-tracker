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


def extract_tables(pdf_path: str, max_pages: int | None = 20) -> List[List[List[str | None]]]:
    """
    Extract tables from PDF using pdfplumber.
    Returns a list of tables; each table is a list of rows; each row is a list of cell strings.
    Useful for UCO/HDFC/SBI-style bank statements with tabular layout.
    """
    import pdfplumber

    all_tables: List[List[List[str | None]]] = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        n = min(total, max_pages) if max_pages else total
        for i in range(n):
            page = pdf.pages[i]
            tables = page.extract_tables() or []
            for t in tables:
                if t and len(t) > 0:
                    # Normalize cells: None -> "", ensure strings
                    rows = [
                        [str(c).strip() if c is not None else "" for c in row]
                        for row in t
                    ]
                    all_tables.append(rows)
    return all_tables

