"""
Unit tests for the canonical clause categories definition.
Guards against accidental edits, reordering, duplicate labels, or count drift.
"""

from backend.ml.categories import CATEGORIES
from backend.ml.classifier import ClauseClassifier


def test_categories_count_and_uniqueness():
    """Verify CATEGORIES has exactly 15 unique, non-empty string entries."""
    assert isinstance(CATEGORIES, list), "CATEGORIES must be a list"
    assert len(CATEGORIES) == 15, f"Expected 15 categories, found {len(CATEGORIES)}"
    assert len(set(CATEGORIES)) == 15, "All category entries must be unique"
    for cat in CATEGORIES:
        assert isinstance(cat, str), f"Category entry {cat!r} must be a str"
        assert cat.strip(), "Category entry cannot be empty"


def test_categories_expected_order_and_content():
    """Verify the exact canonical list of 15 commercial clause categories."""
    expected = [
        "Termination",
        "Indemnification",
        "Limitation_of_Liability",
        "Confidentiality",
        "Non_Compete",
        "Governing_Law",
        "Dispute_Resolution",
        "Intellectual_Property",
        "Payment_Terms",
        "Term_and_Renewal",
        "Warranties",
        "Exclusivity_and_Non_Solicit",
        "Severability",
        "Force_Majeure",
        "Assignment",
    ]
    assert CATEGORIES == expected, "CATEGORIES does not match canonical order or content"


def test_classifier_service_uses_canonical_categories():
    """Ensure ClauseClassifier references the same canonical CATEGORIES object."""
    classifier = ClauseClassifier()
    assert classifier.categories == CATEGORIES
