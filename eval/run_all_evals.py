"""
Master Evaluation Suite Runner for LegalLens (Phase 8).
Executes:
1. Clause Classification Benchmark (Precision, Recall, Macro-F1)
2. Risk-Flag Accuracy & Traceability Comparison
3. Grounded QA & Citation Quality Review
4. Indian Jurisdictional Transfer Sanity Check
Consolidates metrics and writes to eval/results/.
"""

import os
import sys
import json
from datetime import datetime

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from eval.eval_classifier import run_classification_eval
from eval.eval_risk import run_risk_eval
from eval.eval_qa import run_qa_eval
from eval.eval_indian_transfer import run_indian_transfer_eval


def run_master_eval():
    os.makedirs("eval/results", exist_ok=True)
    print("=" * 70)
    print("Starting LegalLens Master Evaluation Suite...")
    print("=" * 70)

    # 1. Classification
    print("\n[1/4] Running Clause Classification Benchmark on CUAD...")
    cls_res = run_classification_eval()

    # 2. Risk Flags
    print("\n[2/4] Running Risk Assessment Engine Accuracy Benchmark...")
    risk_res = run_risk_eval()

    # 3. QA Quality
    print("\n[3/4] Running Grounded QA Quality & Citation Correctness Benchmark...")
    qa_res = run_qa_eval()

    # 4. Indian Transfer
    print("\n[4/4] Running Indian Contract Jurisdictional Transfer Sanity Check...")
    ind_res = run_indian_transfer_eval()

    # Consolidate
    summary = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "system": "LegalLens AI Platform (Academic MCA Mini Project)",
        "metrics_summary": {
            "classification": {
                "dataset": cls_res["dataset"],
                "total_samples": cls_res["total_samples"],
                "accuracy": cls_res["accuracy"],
                "macro_f1": cls_res["macro_f1"],
                "macro_precision": cls_res["macro_precision"],
                "macro_recall": cls_res["macro_recall"],
            },
            "risk_engine": {
                "total_clauses_tested": risk_res["total_test_clauses"],
                "sensitivity_recall": risk_res["sensitivity_recall"],
                "specificity": risk_res["specificity"],
                "precision": risk_res["precision"],
                "traceability_rate": risk_res["traceability_rate"],
            },
            "grounded_qa": {
                "total_queries_tested": qa_res["total_queries_tested"],
                "citation_accuracy": qa_res["citation_accuracy"],
                "out_of_scope_refusal_accuracy": qa_res["out_of_scope_refusal_accuracy"],
                "hallucination_rate": qa_res["hallucination_rate"],
                "disclaimer_compliance": qa_res["disclaimer_compliance"],
            },
            "indian_jurisdictional_transfer": {
                "category_transfer_accuracy": ind_res["category_transfer_accuracy"],
                "status": ind_res["status"],
                "findings_count": len(ind_res["key_documented_findings"]),
            }
        },
        "detailed_evaluations": {
            "classification": cls_res,
            "risk_engine": risk_res,
            "grounded_qa": qa_res,
            "indian_transfer": ind_res,
        }
    }

    # Save JSON summary
    json_path = os.path.join("eval", "results", "evaluation_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Generate Markdown Summary
    md_content = f"""# LegalLens — Comprehensive Evaluation Results Report

> **Evaluation Executed**: {summary['timestamp']}  
> **Platform**: LegalLens AI Contract Intelligence (MCA Academic Mini Project)

---

## 1. Executive Metric Summary

| Evaluation Dimension | Benchmark / Scope | Key Metric | Result | Target / Standard |
| :--- | :--- | :--- | :---: | :---: |
| **Clause Classification** | CUAD 15-Core Categories | **Macro-F1** | **{cls_res['macro_f1']}** | > 0.85 |
| | | **Accuracy** | **{cls_res['accuracy'] * 100:.1f}%** | > 85% |
| | | **Macro-Precision** | **{cls_res['macro_precision']}** | > 0.85 |
| | | **Macro-Recall** | **{cls_res['macro_recall']}** | > 0.85 |
| **Risk Assessment Engine** | Predatory vs Balanced Suite | **Sensitivity (Recall)** | **{risk_res['sensitivity_recall'] * 100:.1f}%** | > 90% |
| | | **Specificity** | **{risk_res['specificity'] * 100:.1f}%** | > 90% |
| | | **Traceability Rate** | **{risk_res['traceability_rate'] * 100:.1f}%** | 100.0% (Constitution) |
| **Grounded QA Engine** | Grounded Conversational RAG | **Citation Accuracy** | **{qa_res['citation_accuracy'] * 100:.1f}%** | > 90% |
| | | **Out-of-Scope Refusal** | **{qa_res['out_of_scope_refusal_accuracy'] * 100:.1f}%** | 100.0% (Constitution) |
| | | **Hallucination Rate** | **{qa_res['hallucination_rate'] * 100:.1f}%** | 0.0% |
| | | **Disclaimer Compliance**| **{qa_res['disclaimer_compliance'] * 100:.1f}%** | 100.0% (Constitution) |
| **Indian Transfer Sanity** | Real Indian Contract Clauses| **Category Transfer** | **{ind_res['category_transfer_accuracy'] * 100:.1f}%** | Empirical Assessment |

---

## 2. Indian Jurisdictional Transfer Findings
The base literature fine-tuning legal models on US datasets (CUAD) never validates jurisdictional transfer to Indian contracts. LegalLens documents these empirical findings:

1. **Common-Law Linguistic Alignment**: InLegalBERT achieves **{ind_res['category_transfer_accuracy'] * 100:.1f}%** accuracy in transferring category labels across Indian contracts (Arbitration, Governing Law, Payment/TDS, and Termination).
2. **Statutory Divergence under Section 27**: Under Section 27 of the Indian Contract Act 1872, post-employment restrictive covenants are **void ab initio**, whereas US CUAD benchmarks evaluate them under reasonableness standards.
3. **Liquidated Damages Formalities**: Under Section 74 of the Indian Contract Act, employment bond penalties require proof of actual damages incurred, rather than unilateral forfeiture.
4. **Stamp Duty Admissibility**: Specific state stamp acts (e.g. Karnataka Stamp Act 1957) impose document admissibility conditions that have no analog in US commercial training sets.

---

*Report automatically generated by LegalLens Evaluation Suite.*
"""
    md_path = os.path.join("eval", "results", "evaluation_summary.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print("\n" + "=" * 70)
    print("Master Evaluation Complete!")
    print(f"Results written to:\n  - {json_path}\n  - {md_path}")
    print("=" * 70)
    return summary


if __name__ == "__main__":
    run_master_eval()
