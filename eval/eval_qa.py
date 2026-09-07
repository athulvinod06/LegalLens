"""
Evaluation Harness — QA Quality & Citation Correctness Benchmark (Phase 8).
Evaluates answer relevance, citation accuracy, out-of-scope refusal adherence,
and hallucination rate on sample queries.
Writes results to eval/results/qa_quality_metrics.json.
"""

import os
import sys
import json
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ml.vector_store import ContractVectorStore
from backend.ml.qa_engine import GroundedQAEngine
from backend.ml.classifier import ClassifiedClause

REFERENCE_CLAUSES = [
    ClassifiedClause(
        clause_id=1, clause_number="1.", title="Scope of Services",
        text="Contractor shall build an AI-powered contract analysis platform using FastAPI and React.",
        category="General_Provisions", confidence=0.92
    ),
    ClassifiedClause(
        clause_id=2, clause_number="2.", title="Payment Terms",
        text="Client agrees to pay Contractor a total fee of $12,000 within 15 days of milestone approval.",
        category="Payment_Terms", confidence=0.96
    ),
    ClassifiedClause(
        clause_id=3, clause_number="3.", title="Termination for Convenience",
        text="Either party may terminate this agreement at any time by giving fourteen (14) days prior written notice.",
        category="Termination", confidence=0.95
    ),
    ClassifiedClause(
        clause_id=4, clause_number="4.", title="Limitation of Liability",
        text="In no event shall either party's maximum aggregate liability exceed the total amounts paid under this contract.",
        category="Limitation_of_Liability", confidence=0.94
    ),
    ClassifiedClause(
        clause_id=5, clause_number="5.", title="Confidentiality",
        text="Recipient agrees to protect all proprietary technical specifications for a period of two (2) years.",
        category="Confidentiality", confidence=0.95
    ),
]

QA_TEST_CASES = [
    # In-Scope Grounded Queries
    {
        "question": "How can the agreement be terminated and what is the required notice period?",
        "expected_in_scope": True,
        "expected_citation": 3,
        "expected_key_facts": ["14", "days", "notice"],
    },
    {
        "question": "What is the total fee and payment timeline?",
        "expected_in_scope": True,
        "expected_citation": 2,
        "expected_key_facts": ["$12,000", "15 days"],
    },
    {
        "question": "What is the liability cap under this contract?",
        "expected_in_scope": True,
        "expected_citation": 4,
        "expected_key_facts": ["maximum aggregate liability", "total amounts paid"],
    },
    {
        "question": "How long do confidentiality obligations last?",
        "expected_in_scope": True,
        "expected_citation": 5,
        "expected_key_facts": ["two (2) years", "proprietary"],
    },
    # Out-of-Scope Ungrounded Queries (Must Be Refused!)
    {
        "question": "Does this contract permit dogs or pets on company premises?",
        "expected_in_scope": False,
        "expected_citation": None,
        "expected_key_facts": ["does not address"],
    },
    {
        "question": "Are payments acceptable in Bitcoin or Ethereum cryptocurrency?",
        "expected_in_scope": False,
        "expected_citation": None,
        "expected_key_facts": ["does not address"],
    },
    {
        "question": "What is the company policy regarding paid parental leave?",
        "expected_in_scope": False,
        "expected_citation": None,
        "expected_key_facts": ["does not address"],
    },
]


def run_qa_eval() -> Dict[str, Any]:
    """Evaluates QA grounding, citation precision, and refusal fidelity."""
    store = ContractVectorStore()
    eval_user = "eval_qa_user"
    eval_contract = "eval_contract_01"
    store.index_clauses(user_id=eval_user, contract_id=eval_contract, clauses=REFERENCE_CLAUSES)
    qa_engine = GroundedQAEngine(vector_store=store)

    correct_citations = 0
    in_scope_count = 0
    correct_refusals = 0
    out_of_scope_count = 0
    disclaimer_count = 0
    hallucinations = 0

    evaluated_queries = []

    for test in QA_TEST_CASES:
        q = test["question"]
        resp = qa_engine.answer_question(eval_user, eval_contract, q)

        has_disclaimer = "not legal advice" in resp.disclaimer.lower()
        if has_disclaimer:
            disclaimer_count += 1

        if test["expected_in_scope"]:
            in_scope_count += 1
            # Check citation correctness
            has_correct_citation = (test["expected_citation"] in resp.citations)
            if has_correct_citation:
                correct_citations += 1
            # Check factual grounding
            grounded = any(k.lower() in resp.answer.lower() for k in test["expected_key_facts"])
            if not grounded:
                hallucinations += 1

            evaluated_queries.append({
                "question": q,
                "type": "in_scope",
                "answer": resp.answer,
                "citations": resp.citations,
                "citation_correct": has_correct_citation,
                "is_grounded": resp.is_grounded,
            })
        else:
            out_of_scope_count += 1
            # Expected refusal
            refused = (not resp.is_grounded) and ("does not address" in resp.answer.lower())
            if refused:
                correct_refusals += 1
            else:
                hallucinations += 1

            evaluated_queries.append({
                "question": q,
                "type": "out_of_scope",
                "answer": resp.answer,
                "correct_refusal": refused,
                "is_grounded": resp.is_grounded,
            })

    citation_accuracy = round(correct_citations / in_scope_count, 3) if in_scope_count > 0 else 1.0
    refusal_accuracy = round(correct_refusals / out_of_scope_count, 3) if out_of_scope_count > 0 else 1.0
    hallucination_rate = round(hallucinations / len(QA_TEST_CASES), 3)
    disclaimer_compliance = round(disclaimer_count / len(QA_TEST_CASES), 3)

    results = {
        "benchmark": "Grounded QA & Citation Correctness",
        "total_queries_tested": len(QA_TEST_CASES),
        "in_scope_queries": in_scope_count,
        "out_of_scope_queries": out_of_scope_count,
        "citation_accuracy": citation_accuracy,
        "out_of_scope_refusal_accuracy": refusal_accuracy,
        "hallucination_rate": hallucination_rate,
        "disclaimer_compliance": disclaimer_compliance,
        "evaluated_queries": evaluated_queries,
    }

    os.makedirs("eval/results", exist_ok=True)
    out_path = os.path.join("eval", "results", "qa_quality_metrics.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    res = run_qa_eval()
    print("QA Engine Evaluation Complete:")
    print(f"  Citation Accuracy: {res['citation_accuracy'] * 100:.1f}%")
    print(f"  Refusal Accuracy (Out-of-Scope): {res['out_of_scope_refusal_accuracy'] * 100:.1f}%")
    print(f"  Hallucination Rate: {res['hallucination_rate'] * 100:.1f}%")
    print(f"  Disclaimer Compliance: {res['disclaimer_compliance'] * 100:.1f}%")
