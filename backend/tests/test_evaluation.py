"""
Unit tests for LegalLens Evaluation Harness (Phase 8).
Verifies that all 4 evaluation benchmark routines execute and produce compliant metrics.
"""

from eval.eval_classifier import run_classification_eval
from eval.eval_risk import run_risk_eval
from eval.eval_qa import run_qa_eval
from eval.eval_indian_transfer import run_indian_transfer_eval


def test_eval_classifier_routine():
    """Verify classification evaluation produces precision, recall, and macro-F1 metrics."""
    res = run_classification_eval()
    assert res["total_samples"] > 0
    assert 0.0 <= res["macro_f1"] <= 1.0
    assert 0.0 <= res["macro_precision"] <= 1.0
    assert 0.0 <= res["macro_recall"] <= 1.0
    assert res["accuracy"] >= 0.75


def test_eval_risk_engine_routine():
    """Verify risk evaluation measures sensitivity, specificity, and 100% traceability."""
    res = run_risk_eval()
    assert res["total_test_clauses"] > 0
    assert res["sensitivity_recall"] >= 0.90
    assert res["specificity"] >= 0.90
    assert res["traceability_rate"] == 1.0  # Constitutional non-negotiable


def test_eval_qa_quality_routine():
    """Verify QA evaluation achieves high citation accuracy and zero hallucination rate."""
    res = run_qa_eval()
    assert res["citation_accuracy"] >= 0.80
    assert res["out_of_scope_refusal_accuracy"] == 1.0  # Must refuse ungrounded questions
    assert res["hallucination_rate"] == 0.0
    assert res["disclaimer_compliance"] == 1.0


def test_eval_indian_jurisdictional_transfer_routine():
    """Verify Indian contract transfer evaluation produces documented findings."""
    res = run_indian_transfer_eval()
    assert 0.0 <= res["category_transfer_accuracy"] <= 1.0
    assert len(res["key_documented_findings"]) >= 3
    assert len(res["clause_evaluations"]) == 5
