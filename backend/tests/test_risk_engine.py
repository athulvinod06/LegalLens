"""
Unit tests for Risk Assessment Engine (Phase 4).
"""

from backend.ml.risk_engine import RiskAssessmentEngine
from backend.ml.classifier import ClassifiedClause


def test_balanced_contract_scoring():
    """Verify that a balanced contract with all required clauses has a high score and Low Risk."""
    engine = RiskAssessmentEngine()
    clauses = [
        ClassifiedClause(clause_id=1, clause_number="1.", title="Payment", text="Client shall pay Contractor within 30 days of invoice receipt.", category="Payment_Terms", confidence=0.95),
        ClassifiedClause(clause_id=2, clause_number="2.", title="IP", text="Contractor assigns ownership of agreed deliverables upon full payment.", category="Intellectual_Property", confidence=0.95),
        ClassifiedClause(clause_id=3, clause_number="3.", title="Termination", text="Either party may terminate upon 30 days prior written notice.", category="Termination", confidence=0.92),
        ClassifiedClause(clause_id=4, clause_number="4.", title="Liability", text="Each party's liability shall be capped at the total amount paid under this agreement.", category="Limitation_of_Liability", confidence=0.90),
    ]
    report = engine.evaluate_contract(clauses, contract_type="freelance")
    assert report.overall_score >= 80.0
    assert report.risk_level == "Low Risk"
    assert len(report.omissions) == 0


def test_unilateral_termination_heuristic():
    """Verify unilateral termination for convenience triggers RULE_UNILATERAL_TERMINATION with clause traceability."""
    engine = RiskAssessmentEngine()
    clauses = [
        ClassifiedClause(
            clause_id=14,
            clause_number="Section 14",
            title="Termination",
            text="Company may at its option terminate this contract at any time without cause and without notice.",
            category="Termination",
            confidence=0.95,
        )
    ]
    report = engine.evaluate_contract(clauses, contract_type="employment")
    
    # Assert rule triggered
    flag_rules = [f.rule_id for f in report.flags]
    assert "RULE_UNILATERAL_TERMINATION" in flag_rules

    # Find the specific flag and assert strict traceability
    term_flag = next(f for f in report.flags if f.rule_id == "RULE_UNILATERAL_TERMINATION")
    assert term_flag.clause_id == 14
    assert term_flag.clause_number == "Section 14"
    assert term_flag.severity == "HIGH"
    assert term_flag.deduction_points > 15.0
    assert len(term_flag.explanation) > 0
    assert len(term_flag.recommendation) > 0


def test_uncapped_indemnification_heuristic():
    """Verify broad uncapped indemnity is flagged with specific clause citation."""
    engine = RiskAssessmentEngine()
    clauses = [
        ClassifiedClause(
            clause_id=7,
            clause_number="Clause 7",
            title="Indemnity",
            text="Contractor shall defend, indemnify, and hold harmless Client against any and all claims, damages, losses, and liabilities whatsoever.",
            category="Indemnification",
            confidence=0.96,
        )
    ]
    report = engine.evaluate_contract(clauses, contract_type="freelance")
    flag_rules = [f.rule_id for f in report.flags]
    assert "RULE_UNCAPPED_INDEMNIFICATION" in flag_rules
    
    flag = next(f for f in report.flags if f.rule_id == "RULE_UNCAPPED_INDEMNIFICATION")
    assert flag.clause_id == 7
    assert flag.severity == "HIGH"


def test_checklist_omissions_audit():
    """Verify that missing required contract clauses are identified as omissions."""
    engine = RiskAssessmentEngine()
    # Contract with only a confidentiality clause (missing Payment_Terms, IP, Termination, Limitation of Liability)
    clauses = [
        ClassifiedClause(
            clause_id=1,
            clause_number="1.",
            title="NDA",
            text="Recipient shall keep all project details strictly confidential.",
            category="Confidentiality",
            confidence=0.90,
        )
    ]
    report = engine.evaluate_contract(clauses, contract_type="freelance")
    assert "Payment_Terms" in report.omissions
    assert "Intellectual_Property" in report.omissions
    assert "Termination" in report.omissions
    assert "Limitation_of_Liability" in report.omissions
    
    # Check that omission flags are generated
    omission_rules = [f.rule_id for f in report.flags if f.rule_id.startswith("OMISSION_")]
    assert len(omission_rules) >= 4


def test_predatory_contract_overall_score():
    """Verify that multiple severe predatory terms compound and result in a High Risk score."""
    engine = RiskAssessmentEngine()
    clauses = [
        ClassifiedClause(
            clause_id=1,
            text="Client reserves the right to terminate at any time without cause or notice.",
            category="Termination",
            confidence=0.95
        ),
        ClassifiedClause(
            clause_id=2,
            text="Contractor shall defend and hold harmless Client against any and all claims whatsoever.",
            category="Indemnification",
            confidence=0.95
        ),
        ClassifiedClause(
            clause_id=3,
            text="In no event shall Client be liable for any damages under any circumstances.",
            category="Limitation_of_Liability",
            confidence=0.92
        ),
        ClassifiedClause(
            clause_id=4,
            text="Contractor shall not engage in any competing business anywhere in the world for a period of five years.",
            category="Non_Compete",
            confidence=0.95
        ),
    ]
    report = engine.evaluate_contract(clauses, contract_type="freelance")
    assert report.overall_score < 50.0
    assert report.risk_level == "High Risk"
    assert report.flags_count >= 4
