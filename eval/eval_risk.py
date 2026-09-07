"""
Evaluation Harness — Risk Assessment Engine Accuracy Benchmark (Phase 8).
Evaluates true positive, false positive, and traceability rates on a labeled
test suite of predatory vs balanced clauses.
Writes results to eval/results/risk_flag_metrics.json.
"""

import os
import sys
import json
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ml.risk_engine import risk_engine_service
from backend.ml.classifier import ClassifiedClause

RISK_BENCHMARK_CASES = [
    # True Positives (Known predatory / high-risk terms)
    {
        "clause_id": 1,
        "text": "Company reserves the sole discretion to terminate this agreement at any time without cause and with immediate effect.",
        "category": "Termination",
        "expected_risk": True,
        "expected_rule": "RULE_UNILATERAL_TERMINATION",
    },
    {
        "clause_id": 2,
        "text": "Contractor shall defend, indemnify and hold harmless Company from any and all claims, losses, and damages whatsoever.",
        "category": "Indemnification",
        "expected_risk": True,
        "expected_rule": "RULE_UNCAPPED_INDEMNIFICATION",
    },
    {
        "clause_id": 3,
        "text": "In no event shall Employer under any circumstances be liable for any damages of any kind.",
        "category": "Limitation_of_Liability",
        "expected_risk": True,
        "expected_rule": "RULE_TOTAL_LIABILITY_DISCLAIMER",
    },
    {
        "clause_id": 4,
        "text": "Employee covenants not to engage in competing business anywhere in the world for a period of five years.",
        "category": "Non_Compete",
        "expected_risk": True,
        "expected_rule": "RULE_EXCESSIVE_NON_COMPETE",
    },
    {
        "clause_id": 5,
        "text": "Client may amend this agreement at any time in its sole discretion without notice.",
        "category": "General_Provisions",
        "expected_risk": True,
        "expected_rule": "RULE_UNILATERAL_MODIFICATION",
    },
    {
        "clause_id": 6,
        "text": "Unpaid amounts shall incur an exorbitant late fee of 25% per month penalty.",
        "category": "Payment_Terms",
        "expected_risk": True,
        "expected_rule": "RULE_EXORBITANT_LATE_FEE",
    },
    # True Negatives (Balanced, fair commercial clauses that should NOT be flagged as predatory)
    {
        "clause_id": 7,
        "text": "Either party may terminate this agreement upon thirty (30) days prior written notice.",
        "category": "Termination",
        "expected_risk": False,
        "expected_rule": None,
    },
    {
        "clause_id": 8,
        "text": "Each party agrees to indemnify the other solely against third-party claims arising from gross negligence.",
        "category": "Indemnification",
        "expected_risk": False,
        "expected_rule": None,
    },
    {
        "clause_id": 9,
        "text": "Each party's maximum aggregate liability shall not exceed the total fees paid under this agreement in the preceding 12 months.",
        "category": "Limitation_of_Liability",
        "expected_risk": False,
        "expected_rule": None,
    },
    {
        "clause_id": 10,
        "text": "Client shall pay Contractor within thirty (30) days of receiving an undisputed invoice.",
        "category": "Payment_Terms",
        "expected_risk": False,
        "expected_rule": None,
    },
    {
        "clause_id": 11,
        "text": "This agreement may only be amended in writing signed by authorized representatives of both parties.",
        "category": "General_Provisions",
        "expected_risk": False,
        "expected_rule": None,
    },
]


def run_risk_eval() -> Dict[str, Any]:
    """Evaluates risk detection sensitivity, specificity, and traceability."""
    tp, fp, tn, fn = 0, 0, 0, 0
    traceable_flags = 0
    total_flags = 0

    evaluated_cases = []

    for item in RISK_BENCHMARK_CASES:
        clause = ClassifiedClause(
            clause_id=item["clause_id"],
            clause_number=f"Clause {item['clause_id']}",
            text=item["text"],
            category=item["category"],
            confidence=0.95
        )
        report = risk_engine_service.evaluate_contract([clause], contract_type="freelance")
        clause_flags = [f for f in report.flags if f.clause_id == item["clause_id"]]

        is_flagged = len(clause_flags) > 0
        total_flags += len(clause_flags)
        for f in clause_flags:
            if f.clause_id and f.rule_id and f.deduction_points > 0:
                traceable_flags += 1

        if item["expected_risk"]:
            if is_flagged:
                tp += 1
                matched_rule = any(f.rule_id == item["expected_rule"] for f in clause_flags)
            else:
                fn += 1
                matched_rule = False
        else:
            if is_flagged:
                fp += 1
                matched_rule = False
            else:
                tn += 1
                matched_rule = True

        evaluated_cases.append({
            "clause_id": item["clause_id"],
            "expected_risk": item["expected_risk"],
            "flagged": is_flagged,
            "matched_expected_rule": matched_rule,
            "flags": [f.rule_id for f in clause_flags]
        })

    sensitivity = round(tp / (tp + fn), 3) if (tp + fn) > 0 else 1.0
    specificity = round(tn / (tn + fp), 3) if (tn + fp) > 0 else 1.0
    precision = round(tp / (tp + fp), 3) if (tp + fp) > 0 else 1.0
    traceability_rate = round(traceable_flags / total_flags, 3) if total_flags > 0 else 1.0

    results = {
        "benchmark": "Predatory vs Balanced Clause Detection",
        "total_test_clauses": len(RISK_BENCHMARK_CASES),
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "sensitivity_recall": sensitivity,
        "specificity": specificity,
        "precision": precision,
        "traceability_rate": traceability_rate,
        "evaluated_cases": evaluated_cases
    }

    os.makedirs("eval/results", exist_ok=True)
    out_path = os.path.join("eval", "results", "risk_flag_metrics.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    res = run_risk_eval()
    print("Risk Engine Evaluation Complete:")
    print(f"  Sensitivity (Recall): {res['sensitivity_recall'] * 100:.1f}%")
    print(f"  Specificity: {res['specificity'] * 100:.1f}%")
    print(f"  Precision: {res['precision'] * 100:.1f}%")
    print(f"  Traceability Rate: {res['traceability_rate'] * 100:.1f}%")
