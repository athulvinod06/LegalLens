"""
Unit tests for Clause Segmentation Service (Phase 2).
"""

from backend.app.services.segmenter import segment_into_clauses


def test_segment_numbered_contract():
    """Verify contracts with standard 1., 2., 3. numbering split into exact clause count."""
    contract_text = """
    EMPLOYMENT AGREEMENT

    1. Position and Duties
    Employee agrees to work as Lead Software Engineer for Employer.

    2. Compensation and Benefits
    Employer shall pay Employee an annual base salary of $120,000 payable semi-monthly.

    3. Termination
    Either party may terminate this agreement upon thirty (30) days written notice.

    4. Governing Law
    This Agreement shall be governed by the laws of the State of Delaware.
    """
    clauses = segment_into_clauses(contract_text)
    # 4 distinct numbered clauses (and potentially preamble)
    assert len(clauses) >= 4
    # Check that clauses have IDs and non-empty text
    for c in clauses:
        assert c.clause_id > 0
        assert len(c.text) > 0
        assert c.word_count > 0

    # Verify specific clause titles or numbers
    clause_texts = [c.text for c in clauses]
    assert any("Compensation and Benefits" in t for t in clause_texts)
    assert any("Termination" in t for t in clause_texts)


def test_segment_section_style_contract():
    """Verify Section 1, Section 2 style contract segmentation."""
    contract_text = """
    Section 1. Definitions.
    'Confidential Information' refers to all proprietary code and commercial strategies.

    Section 2. Non-Disclosure Obligations.
    The Receiving Party shall preserve confidentiality with reasonable care.

    Section 3. Limitation of Liability.
    Neither party will be liable for indirect or consequential damages.
    """
    clauses = segment_into_clauses(contract_text)
    assert len(clauses) == 3
    assert clauses[0].clause_id == 1
    assert clauses[1].clause_id == 2
    assert clauses[2].clause_id == 3
    assert "Definitions" in clauses[0].text
    assert "Non-Disclosure" in clauses[1].text
    assert "Limitation of Liability" in clauses[2].text


def test_segment_article_style_contract():
    """Verify Article I, Article II style contract segmentation."""
    contract_text = """
    ARTICLE I - TERM AND TERMINATION
    This Lease shall commence on October 1, 2026 and continue for twelve (12) months.

    ARTICLE II - RENT
    Tenant shall pay Landlord $2,500 on the first day of each calendar month.

    ARTICLE III - MAINTENANCE
    Landlord agrees to maintain structural components in good repair.
    """
    clauses = segment_into_clauses(contract_text)
    assert len(clauses) == 3
    assert "ARTICLE I" in clauses[0].text
    assert "ARTICLE II" in clauses[1].text
    assert "ARTICLE III" in clauses[2].text


def test_segment_all_caps_headings():
    """Verify contracts using unnumbered capitalized titles segment properly."""
    contract_text = """
    CONFIDENTIALITY
    Recipient agrees not to disclose trade secrets.

    INDEMNIFICATION
    Consultant shall defend and indemnify Client against IP infringement claims.

    SEVERABILITY
    If any provision is invalid, the remainder continues in full effect.
    """
    clauses = segment_into_clauses(contract_text)
    assert len(clauses) == 3
    assert "CONFIDENTIALITY" in clauses[0].text
    assert "INDEMNIFICATION" in clauses[1].text
    assert "SEVERABILITY" in clauses[2].text


def test_segment_unformatted_paragraph_fallback():
    """Verify fallback splitting on paragraphs when no explicit headings exist."""
    contract_text = """
    This is paragraph one explaining the partnership intent.

    This is paragraph two detailing the profit split between the partners.

    This is paragraph three describing how disputes will be settled.
    """
    clauses = segment_into_clauses(contract_text)
    assert len(clauses) == 3
    assert clauses[0].clause_id == 1
    assert clauses[1].clause_id == 2
    assert clauses[2].clause_id == 3
