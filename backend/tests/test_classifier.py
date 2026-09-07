"""
Unit tests for Clause Classification Service (Phase 3).
"""

from backend.ml.classifier import ClauseClassifier, CATEGORIES
from backend.app.services.segmenter import SegmentedClause


def test_classifier_categories_count():
    """Verify that exactly 15 core categories are defined as per specification."""
    classifier = ClauseClassifier()
    assert len(classifier.categories) == 15
    assert "Termination" in classifier.categories
    assert "Indemnification" in classifier.categories
    assert "Limitation_of_Liability" in classifier.categories
    assert "Non_Compete" in classifier.categories


def test_classify_termination():
    classifier = ClauseClassifier()
    text = "Either party may terminate this Agreement without cause upon 30 days prior written notice."
    category, conf = classifier.classify_text(text, title="Termination for Convenience")
    assert category == "Termination"
    assert 0.80 <= conf <= 1.0


def test_classify_indemnification():
    classifier = ClauseClassifier()
    text = "Contractor agrees to defend, indemnify, and hold harmless Company from any third-party claims."
    category, conf = classifier.classify_text(text, title="Indemnity")
    assert category == "Indemnification"
    assert 0.85 <= conf <= 1.0


def test_classify_limitation_of_liability():
    classifier = ClauseClassifier()
    text = "In no event shall either party's maximum aggregate liability exceed the total fees paid under this agreement."
    category, conf = classifier.classify_text(text, title="Liability Cap")
    assert category == "Limitation_of_Liability"
    assert 0.85 <= conf <= 1.0


def test_classify_confidentiality():
    classifier = ClauseClassifier()
    text = "The Receiving Party shall maintain in strict confidence all proprietary trade secrets and technical data."
    category, conf = classifier.classify_text(text, title="Non-Disclosure")
    assert category == "Confidentiality"
    assert 0.85 <= conf <= 1.0


def test_classify_non_compete():
    classifier = ClauseClassifier()
    text = "During the term and for 12 months following termination, Employee shall not engage in any competing business."
    category, conf = classifier.classify_text(text, title="Restrictive Covenants")
    assert category == "Non_Compete"
    assert 0.85 <= conf <= 1.0


def test_classify_intellectual_property():
    classifier = ClauseClassifier()
    text = "All deliverables developed hereunder shall constitute a work made for hire and Contractor assigns all patent and copyright rights."
    category, conf = classifier.classify_text(text, title="IP Rights")
    assert category == "Intellectual_Property"
    assert 0.85 <= conf <= 1.0


def test_batch_classification():
    classifier = ClauseClassifier()
    clauses = [
        SegmentedClause(clause_id=1, clause_number="1.", title="Term", text="The initial term shall be 1 year.", word_count=7),
        SegmentedClause(clause_id=2, clause_number="2.", title="Governing Law", text="This contract shall be governed by the laws of New York.", word_count=10),
        SegmentedClause(clause_id=3, clause_number="3.", title="Force Majeure", text="Neither party is liable for acts of God or unforeseen disasters.", word_count=11),
    ]
    results = classifier.classify_clauses(clauses)
    assert len(results) == 3
    assert results[0].category == "Term_and_Renewal"
    assert results[1].category == "Governing_Law"
    assert results[2].category == "Force_Majeure"
    for r in results:
        assert 0.0 <= r.confidence <= 1.0
        assert r.is_core_category is True
