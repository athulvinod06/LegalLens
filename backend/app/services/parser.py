"""
Document Parsing Service for LegalLens.
Extracts structured text from PDF and DOCX documents using PyMuPDF and python-docx.
Validates file formats and rejects empty/scanned documents lacking extractable text.
"""

import io
import os
from typing import List, Optional
from pydantic import BaseModel
import fitz  # PyMuPDF
import docx


class EmptyDocumentError(Exception):
    """Raised when a document contains no extractable digital text."""
    pass


class UnsupportedFileTypeError(Exception):
    """Raised when an uploaded document has an unsupported extension or MIME type."""
    pass


class ParsedDocument(BaseModel):
    filename: str
    file_type: str  # 'pdf' or 'docx'
    page_count: int
    total_characters: int
    text: str
    paragraphs: List[str]


def parse_pdf(file_bytes: bytes, filename: str) -> ParsedDocument:
    """
    Extract structured text from a PDF file using PyMuPDF.
    Preserves paragraph breaks and page boundaries.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Failed to open PDF document: {str(e)}")

    page_count = len(doc)
    paragraphs: List[str] = []
    full_text_chunks: List[str] = []

    for page_idx in range(page_count):
        page = doc[page_idx]
        text = page.get_text("text")
        if text:
            # Normalize whitespace and preserve meaningful paragraphs
            blocks = [p.strip() for p in text.split("\n\n") if p.strip()]
            paragraphs.extend(blocks)
            full_text_chunks.append(text.strip())

    doc.close()

    raw_text = "\n\n".join(paragraphs).strip()
    total_chars = len(raw_text)

    # Validate extractable text (non-whitespace characters)
    if total_chars == 0:
        raise EmptyDocumentError(
            "The uploaded PDF contains no extractable text. "
            "Please ensure the document is a digital contract with selectable text, not a scanned image."
        )

    return ParsedDocument(
        filename=filename,
        file_type="pdf",
        page_count=max(1, page_count),
        total_characters=total_chars,
        text=raw_text,
        paragraphs=paragraphs,
    )


def parse_docx(file_bytes: bytes, filename: str) -> ParsedDocument:
    """
    Extract structured text from a DOCX file using python-docx.
    Preserves heading and paragraph structure.
    """
    try:
        doc_stream = io.BytesIO(file_bytes)
        doc = docx.Document(doc_stream)
    except Exception as e:
        raise ValueError(f"Failed to open DOCX document: {str(e)}")

    paragraphs: List[str] = []
    for p in doc.paragraphs:
        cleaned = p.text.strip()
        if cleaned:
            paragraphs.append(cleaned)

    # Also capture table contents if present
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                paragraphs.append(row_text)

    raw_text = "\n\n".join(paragraphs).strip()
    total_chars = len(raw_text)

    if total_chars == 0:
        raise EmptyDocumentError(
            "The uploaded DOCX contains no extractable text. "
            "Please upload a valid contract with readable content."
        )

    return ParsedDocument(
        filename=filename,
        file_type="docx",
        page_count=max(1, (len(paragraphs) // 10) + 1),  # Estimated page count
        total_characters=total_chars,
        text=raw_text,
        paragraphs=paragraphs,
    )


def parse_document(file_bytes: bytes, filename: str) -> ParsedDocument:
    """
    Main entry point for document extraction.
    Validates file extension and routes to appropriate parser.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        return parse_pdf(file_bytes, filename)
    elif ext in [".docx", ".doc"]:
        if ext == ".doc":
            raise UnsupportedFileTypeError(
                "Legacy .doc format is not supported. Please convert your file to .docx or .pdf."
            )
        return parse_docx(file_bytes, filename)
    else:
        raise UnsupportedFileTypeError(
            f"Unsupported file format '{ext}'. LegalLens supports PDF (.pdf) and Word (.docx) documents."
        )
