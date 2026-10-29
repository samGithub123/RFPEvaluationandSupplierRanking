# -*- coding: utf-8 -*-
"""
documents.py - PDF text extraction for the RFP Evaluation project.

What it is for:
    Turn an uploaded supplier PDF (raw bytes) into clean plain text that the
    evaluation agent can ground its scoring on.

What it does:
    ✅ Reads a PDF from a byte stream using pypdf.
    ✅ Joins all pages and normalizes whitespace.
"""

from io import BytesIO

from pypdf import PdfReader


def extract_text(pdf_bytes: bytes) -> str:
    """Extract and normalize text from a PDF given its raw bytes."""
    reader = PdfReader(BytesIO(pdf_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages)
    return " ".join(text.split())
