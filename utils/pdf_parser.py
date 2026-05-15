# utils/pdf_parser.py
# ─────────────────────────────────────────────────────────────────
# Core PDF parsing utilities.
# Handles text-layer PDFs using pdfplumber.
# Returns structured data — raw text AND table rows.
# ─────────────────────────────────────────────────────────────────

import pdfplumber
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ParsedPage:
    """
    Everything we extracted from a single PDF page.
    """

    page_number: int
    raw_text: str  # Full text dump of the page
    tables: list[list[list[str]]]  # List of tables, each table is rows of cells
    has_text_layer: bool  # False means this page needs OCR
    word_count: int = 0


@dataclass
class ParsedDocument:
    """
    The full output of parsing one PDF file.
    Contains all pages and a confidence assessment.
    """

    file_path: str
    total_pages: int
    pages: list[ParsedPage] = field(default_factory=list)
    confidence: str = "HIGH"  # HIGH / MEDIUM / POOR
    errors: list[str] = field(default_factory=list)
    needs_ocr_pages: list[int] = field(default_factory=list)  # page numbers needing OCR


def _assess_confidence(doc: ParsedDocument) -> str:
    """
    Rates overall extraction quality.

    Rules:
    - If more than 50% of pages need OCR → POOR
    - If any pages need OCR but less than 50% → MEDIUM
    - If no pages need OCR and text was found → HIGH
    """
    if doc.total_pages == 0:
        return "POOR"

    ocr_ratio = len(doc.needs_ocr_pages) / doc.total_pages

    if ocr_ratio > 0.5:
        return "POOR"
    elif ocr_ratio > 0:
        return "MEDIUM"
    else:
        return "HIGH"


def _is_text_layer_present(page: pdfplumber.page.Page) -> bool:
    """
    Detects whether a PDF page has a real text layer or is just an image.

    Strategy: Extract words from the page. If fewer than 10 words found,
    treat the page as image-only and flag for OCR.

    10 words is a conservative threshold — even a sparse bank statement
    header has account number, bank name, date = well over 10 words.
    """
    words = page.extract_words()
    return len(words) >= 10


def parse_pdf(file_path: str) -> ParsedDocument:
    """
    Main entry point for PDF parsing.

    Takes a file path, returns a ParsedDocument with all extracted
    text and tables, plus a confidence score.

    Args:
        file_path: Absolute or relative path to the PDF file.

    Returns:
        ParsedDocument with pages, confidence, and any errors.
    """
    path = Path(file_path)

    # ── Validate file exists ──────────────────────────────────────
    if not path.exists():
        return ParsedDocument(
            file_path=file_path,
            total_pages=0,
            confidence="POOR",
            errors=[f"File not found: {file_path}"],
        )

    if path.suffix.lower() != ".pdf":
        return ParsedDocument(
            file_path=file_path,
            total_pages=0,
            confidence="POOR",
            errors=[f"Not a PDF file: {file_path}"],
        )

    doc = ParsedDocument(file_path=file_path, total_pages=0)

    try:
        with pdfplumber.open(file_path) as pdf:
            doc.total_pages = len(pdf.pages)
            logger.info(f"Opened PDF: {path.name} | Pages: {doc.total_pages}")

            for page_num, page in enumerate(pdf.pages, start=1):

                # ── Check for text layer ──────────────────────────
                has_text = _is_text_layer_present(page)

                if not has_text:
                    # Flag for OCR — we'll handle this in ocr_handler.py
                    doc.needs_ocr_pages.append(page_num)
                    logger.warning(f"Page {page_num}: No text layer — needs OCR")

                    doc.pages.append(
                        ParsedPage(
                            page_number=page_num,
                            raw_text="",
                            tables=[],
                            has_text_layer=False,
                            word_count=0,
                        )
                    )
                    continue

                # ── Extract raw text ──────────────────────────────
                raw_text = page.extract_text() or ""

                # ── Extract tables ────────────────────────────────
                tables = []
                extracted_tables = page.extract_tables()

                if extracted_tables:
                    for table in extracted_tables:
                        # Clean None cells — pdfplumber returns None for empty cells
                        cleaned_table = [
                            [cell if cell is not None else "" for cell in row]
                            for row in table
                            if any(cell for cell in row)  # skip fully empty rows
                        ]
                        if cleaned_table:
                            tables.append(cleaned_table)

                words = page.extract_words()

                parsed_page = ParsedPage(
                    page_number=page_num,
                    raw_text=raw_text,
                    tables=tables,
                    has_text_layer=True,
                    word_count=len(words),
                )

                doc.pages.append(parsed_page)
                logger.info(
                    f"Page {page_num}: {len(words)} words | "
                    f"{len(tables)} table(s) found"
                )

    except Exception as e:
        error_msg = f"Failed to parse {path.name}: {str(e)}"
        logger.error(error_msg)
        doc.errors.append(error_msg)
        doc.confidence = "POOR"
        return doc

    # ── Assess overall confidence ─────────────────────────────────
    doc.confidence = _assess_confidence(doc)
    logger.info(f"Parse complete | Confidence: {doc.confidence}")

    return doc


def print_parse_summary(doc: ParsedDocument) -> None:
    """
    Prints a human-readable summary of a ParsedDocument.
    Use this to inspect results during development.
    """
    print("\n" + "═" * 55)
    print(f"  FILE     : {Path(doc.file_path).name}")
    print(f"  PAGES    : {doc.total_pages}")
    print(f"  CONFIDENCE: {doc.confidence}")

    if doc.needs_ocr_pages:
        print(f"  OCR NEEDED: Pages {doc.needs_ocr_pages}")

    if doc.errors:
        print(f"  ERRORS   : {doc.errors}")

    print("─" * 55)

    for page in doc.pages:
        status = "✅ TEXT" if page.has_text_layer else "⚠️  SCAN"
        print(
            f"  Page {page.page_number} [{status}] | "
            f"Words: {page.word_count} | "
            f"Tables: {len(page.tables)}"
        )

        if page.tables:
            for t_idx, table in enumerate(page.tables):
                print(
                    f"    Table {t_idx + 1}: {len(table)} rows × "
                    f"{len(table[0]) if table else 0} cols"
                )
                # Preview first 3 rows
                for row in table[:3]:
                    print(f"      {row}")
                if len(table) > 3:
                    print(f"      ... ({len(table) - 3} more rows)")

    print("═" * 55 + "\n")
