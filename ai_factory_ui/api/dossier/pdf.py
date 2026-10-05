"""Convert dossier HTML to PDF bytes."""

from __future__ import annotations

from io import BytesIO


def html_to_pdf(html: str) -> bytes:
    from xhtml2pdf import pisa

    buf = BytesIO()
    result = pisa.CreatePDF(html, dest=buf, encoding="utf-8")
    if result.err:
        raise RuntimeError(f"PDF generation failed ({result.err} error segments)")
    data = buf.getvalue()
    if not data:
        raise RuntimeError("PDF generation produced empty output")
    return data
