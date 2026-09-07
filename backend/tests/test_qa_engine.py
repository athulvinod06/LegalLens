"""
Unit tests for Vector Store & Grounded RAG QA Engine (Phase 5).
"""

from backend.ml.vector_store import ContractVectorStore
from backend.ml.qa_engine import GroundedQAEngine
from backend.ml.classifier import ClassifiedClause


def setup_sample_contract():
    store = ContractVectorStore()
    clauses = [
        ClassifiedClause(
            clause_id=1,
            clause_number="Clause 1",
            title="Scope of Services",
            text="Contractor shall build an e-commerce platform using modern React and FastAPI web technologies.",
            category="General_Provisions",
            confidence=0.90,
        ),
        ClassifiedClause(
            clause_id=2,
            clause_number="Clause 2",
            title="Compensation",
            text="Client agrees to pay Contractor a fixed sum of $15,000 in three equal milestones upon delivery.",
            category="Payment_Terms",
            confidence=0.95,
        ),
        ClassifiedClause(
            clause_id=3,
            clause_number="Clause 3",
            title="Termination",
            text="Either party may terminate this agreement with 14 days prior written notice for convenience.",
            category="Termination",
            confidence=0.95,
        ),
        ClassifiedClause(
            clause_id=4,
            clause_number="Clause 4",
            title="Confidentiality",
            text="Contractor agrees to protect proprietary source code and trade secrets for a period of 2 years.",
            category="Confidentiality",
            confidence=0.96,
        ),
    ]
    store.index_clauses(user_id="user_alice", contract_id="contract_101", clauses=clauses)
    return store, GroundedQAEngine(vector_store=store)


def test_user_isolation_in_retrieval():
    """Verify that User Bob cannot retrieve clauses indexed by User Alice."""
    store, qa_engine = setup_sample_contract()
    
    # Alice asks about termination
    results_alice = store.search(user_id="user_alice", contract_id="contract_101", query="termination notice")
    assert len(results_alice) > 0
    assert results_alice[0]["clause_id"] == 3

    # Bob queries the same contract ID with his user ID
    results_bob = store.search(user_id="user_bob", contract_id="contract_101", query="termination notice")
    assert len(results_bob) == 0  # Strict user isolation


def test_qa_grounded_termination_answer():
    """Verify that asking about termination returns an answer citing Clause 3."""
    _, qa_engine = setup_sample_contract()
    resp = qa_engine.answer_question(
        user_id="user_alice",
        contract_id="contract_101",
        question="How can the agreement be terminated and what is the notice period?"
    )
    assert resp.is_grounded is True
    assert 3 in resp.citations
    assert "Clause 3" in resp.answer
    assert "14 days" in resp.answer
    assert "not legal advice" in resp.disclaimer.lower()


def test_qa_grounded_payment_answer():
    """Verify that asking about compensation returns an answer citing Clause 2."""
    _, qa_engine = setup_sample_contract()
    resp = qa_engine.answer_question(
        user_id="user_alice",
        contract_id="contract_101",
        question="What are the payment terms and fees?"
    )
    assert resp.is_grounded is True
    assert 2 in resp.citations
    assert "Clause 2" in resp.answer
    assert "$15,000" in resp.answer


def test_qa_out_of_scope_refusal():
    """Verify strict refusal when asking about topics completely unaddressed in the contract."""
    _, qa_engine = setup_sample_contract()
    resp = qa_engine.answer_question(
        user_id="user_alice",
        contract_id="contract_101",
        question="What is the policy for keeping dogs or pets in the office?"
    )
    assert resp.is_grounded is False
    assert len(resp.citations) == 0
    assert "does not address this question" in resp.answer.lower()
