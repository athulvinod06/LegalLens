"""
Clause Segmentation Service for LegalLens.
Splits parsed contract text into discrete, auditable clause units
using section headings, numbering schemes, and paragraph structure.
"""

import re
from typing import List, Optional
from pydantic import BaseModel


class SegmentedClause(BaseModel):
    clause_id: int
    clause_number: Optional[str] = None
    title: Optional[str] = None
    text: str
    word_count: int


# Comprehensive Regex patterns for contract clause boundaries
CLAUSE_HEADING_PATTERNS = [
    # E.g. "Section 1.1", "SECTION 2", "Section 3:"
    re.compile(r"^(SECTION\s+\d+(\.\d+)*[:.-]?\s*)(.*)", re.IGNORECASE),
    # E.g. "Article I", "ARTICLE 2 -", "Article IV:"
    re.compile(r"^(ARTICLE\s+([IVXLCDM]+|\d+)[:.-]?\s*)(.*)", re.IGNORECASE),
    # E.g. "Clause 1.", "CLAUSE 3:"
    re.compile(r"^(CLAUSE\s+\d+(\.\d+)*[:.-]?\s*)(.*)", re.IGNORECASE),
    # E.g. "1.", "1.1", "1.1.1", "2.0:"
    re.compile(r"^(\d+(\.\d+)+[:.-]?\s+|\d+[:.-]\s+)(.*)", re.IGNORECASE),
    # E.g. "(a)", "(1)", "(i)" at the start of a paragraph
    re.compile(r"^(\([a-zA-Z0-9ivxlcdmIVXLCDM]+\)\s+)(.*)", re.IGNORECASE),
    # All caps short titles like "TERMINATION AND DEFAULT", "INDEMNIFICATION"
    re.compile(r"^([A-Z\s]{4,45})$"),
]


def is_heading_line(line: str) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Checks if a line matches any standard legal clause heading pattern.
    Returns: (is_heading, clause_number_prefix, title_suffix)
    """
    stripped = line.strip()
    if not stripped or len(stripped) > 120:
        return False, None, None

    for pattern in CLAUSE_HEADING_PATTERNS:
        match = pattern.match(stripped)
        if match:
            groups = match.groups()
            if len(groups) >= 3:
                prefix = groups[0].strip()
                title = groups[-1].strip() if groups[-1] else None
                return True, prefix, title
            elif len(groups) == 1:
                # All caps title without number
                return True, None, groups[0].strip().title()

    # Common standalone title keywords
    standalone_keywords = [
        "recitals", "preamble", "definitions", "term", "termination",
        "payment", "compensation", "indemnification", "indemnity",
        "confidentiality", "non-disclosure", "non-compete", "governing law",
        "jurisdiction", "dispute resolution", "intellectual property",
        "severability", "force majeure", "assignment", "warranties",
        "limitation of liability", "miscellaneous", "notices", "entire agreement"
    ]
    if stripped.lower() in standalone_keywords:
        return True, None, stripped.title()

    return False, None, None


def segment_into_clauses(text: str) -> List[SegmentedClause]:
    """
    Segments raw contract text into structured clause units.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [line.strip() for line in text.split("\n") if line.strip()]

    # Check if any line in the entire text is a heading
    has_headings = False
    for p in paragraphs:
        for line in p.split("\n"):
            if is_heading_line(line)[0]:
                has_headings = True
                break
        if has_headings:
            break

    # If no headings exist anywhere, split purely by paragraphs
    if not has_headings:
        clauses = []
        for idx, p in enumerate(paragraphs, start=1):
            clean_p = re.sub(r"\s+", " ", p).strip()
            if clean_p:
                clauses.append(
                    SegmentedClause(
                        clause_id=idx,
                        clause_number=f"{idx}.",
                        title=None,
                        text=clean_p,
                        word_count=len(clean_p.split()),
                    )
                )
        return clauses

    clauses: List[SegmentedClause] = []
    current_number: Optional[str] = None
    current_title: Optional[str] = None
    current_text_lines: List[str] = []

    def flush_clause():
        nonlocal current_number, current_title, current_text_lines
        if current_text_lines:
            clause_content = " ".join(current_text_lines).strip()
            # Clean excessive whitespace
            clause_content = re.sub(r"\s+", " ", clause_content)
            if clause_content:
                cid = len(clauses) + 1
                words = len(clause_content.split())
                clauses.append(
                    SegmentedClause(
                        clause_id=cid,
                        clause_number=current_number,
                        title=current_title,
                        text=clause_content,
                        word_count=words,
                    )
                )
            current_number = None
            current_title = None
            current_text_lines = []

    for paragraph in paragraphs:
        lines = [l.strip() for l in paragraph.split("\n") if l.strip()]
        for line in lines:
            is_heading, number_prefix, title = is_heading_line(line)
            if is_heading:
                # Start of a new clause boundary
                flush_clause()
                current_number = number_prefix
                current_title = title
                # If there is body text on the same line as heading, keep it
                if title and len(title.split()) > 4:
                    # Title is likely a full sentence/clause body
                    current_text_lines.append(line)
                else:
                    current_text_lines.append(line)
            else:
                current_text_lines.append(line)

    flush_clause()

    # Fallback: if no clauses were detected via headings, chunk by paragraph
    if not clauses and paragraphs:
        for idx, p in enumerate(paragraphs, start=1):
            clean_p = re.sub(r"\s+", " ", p).strip()
            if clean_p:
                clauses.append(
                    SegmentedClause(
                        clause_id=idx,
                        clause_number=f"{idx}.",
                        title=None,
                        text=clean_p,
                        word_count=len(clean_p.split()),
                    )
                )

    return clauses
