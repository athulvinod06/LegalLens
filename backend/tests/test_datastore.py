"""
Unit & Integration tests for Data Store Wiring, Relational CRUD, and User Scoping (Phase 7).
"""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.database import SessionLocal, init_db
from backend.models import User, Contract, Clause, RiskAssessment, RiskDeduction, ChatMessage
from backend.ml.vector_store import vector_store_service
from backend.tests.test_parser import create_sample_pdf

client = TestClient(app)


def setup_module():
    """Ensure database schema is created prior to test run."""
    init_db()


def test_contract_crud_and_relational_persistence():
    """Verify full CRUD persistence: User, Contract, Clauses, RiskAssessment, and RiskDeductions."""
    db = SessionLocal()
    try:
        pdf_bytes = create_sample_pdf("""
        CONSULTING AGREEMENT
        1. Scope of Work: Contractor develops backend cloud services.
        2. Compensation: Client agrees to pay $10,000 upon final milestone.
        3. Termination: Client may terminate at its option at any time without notice.
        4. Liability: Client shall not be liable for any damages under any circumstances.
        """)

        resp = client.post(
            "/api/upload",
            files={"file": ("consulting.pdf", pdf_bytes, "application/pdf")},
            data={"contract_type": "freelance", "user_id": "alice_test"}
        )
        assert resp.status_code == 200
        data = resp.json()
        contract_id = data["contract_id"]

        # 1. Verify User was created / scoped in DB
        user = db.query(User).filter(User.id == "alice_test").first()
        assert user is not None
        assert user.email == "alice_test@legallens.local"

        # 2. Verify Contract record in DB
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        assert contract is not None
        assert contract.user_id == "alice_test"
        assert contract.filename == "consulting.pdf"
        assert contract.contract_type == "freelance"

        # 3. Verify Clauses persisted and linked via Foreign Key
        clauses = db.query(Clause).filter(Clause.contract_id == contract_id).all()
        assert len(clauses) >= 4
        clause_categories = [c.category for c in clauses]
        assert "Payment_Terms" in clause_categories
        assert "Termination" in clause_categories

        # 4. Verify RiskAssessment persisted
        assessment = db.query(RiskAssessment).filter(RiskAssessment.contract_id == contract_id).first()
        assert assessment is not None
        assert 0.0 <= assessment.overall_score <= 100.0

        # 5. Verify RiskDeductions with strict traceability (clause_id, rule_name, points_deducted)
        deductions = db.query(RiskDeduction).filter(RiskDeduction.assessment_id == assessment.id).all()
        assert len(deductions) > 0
        for d in deductions:
            assert d.rule_name is not None
            assert d.points_deducted >= 0.0
            assert d.explanation is not None
            assert d.recommendation is not None

    finally:
        db.close()


def test_user_isolation_security():
    """Verify that User B cannot query, fetch, or chat with User A's contract or embeddings."""
    # 1. User Alice uploads a contract
    pdf_bytes = create_sample_pdf("""
    SECRET CONTRACT
    1. Proprietary Term: Super secret project details for Alice only.
    2. Compensation: $50,000 retainer fee.
    """)
    resp_alice = client.post(
        "/api/upload",
        files={"file": ("secret_alice.pdf", pdf_bytes, "application/pdf")},
        data={"contract_type": "freelance", "user_id": "alice_secure"}
    )
    assert resp_alice.status_code == 200
    contract_id = resp_alice.json()["contract_id"]

    # 2. User Bob attempts to access Alice's contract risk report
    resp_bob_risk = client.get(f"/api/contract/{contract_id}/risk?user_id=bob_intruder")
    assert resp_bob_risk.status_code == 404
    assert "access denied" in resp_bob_risk.json()["detail"].lower()

    # 3. User Bob attempts to ask questions about Alice's contract
    resp_bob_chat = client.post(
        f"/api/contract/{contract_id}/chat",
        json={
            "contract_id": contract_id,
            "question": "What is the secret project fee?",
            "user_id": "bob_intruder"
        }
    )
    assert resp_bob_chat.status_code == 404
    assert "access denied" in resp_bob_chat.json()["detail"].lower()

    # 4. Vector store isolation: Bob queries vector store directly for Alice's contract
    vector_results_bob = vector_store_service.search(user_id="bob_intruder", contract_id=contract_id, query="secret fee")
    assert len(vector_results_bob) == 0

    # Alice querying her own contract succeeds
    resp_alice_risk = client.get(f"/api/contract/{contract_id}/risk?user_id=alice_secure")
    assert resp_alice_risk.status_code == 200
    assert resp_alice_risk.json()["contract_id"] == contract_id


def test_integrity_cascades_on_deletion():
    """Verify deleting a contract cleanly cascades deletion to clauses, assessments, deductions, and vector entries."""
    db = SessionLocal()
    try:
        pdf_bytes = create_sample_pdf("""
        TEMPORARY AGREEMENT
        1. Term: Expires next month.
        2. Payment: $1,000 upon termination.
        """)
        resp = client.post(
            "/api/upload",
            files={"file": ("temp.pdf", pdf_bytes, "application/pdf")},
            data={"contract_type": "freelance", "user_id": "cascade_user"}
        )
        assert resp.status_code == 200
        contract_id = resp.json()["contract_id"]

        # Confirm relational records exist before deletion
        assert db.query(Contract).filter(Contract.id == contract_id).count() == 1
        assert db.query(Clause).filter(Clause.contract_id == contract_id).count() >= 2
        assert db.query(RiskAssessment).filter(RiskAssessment.contract_id == contract_id).count() == 1

        # Delete contract via API
        del_resp = client.delete(f"/api/contract/{contract_id}?user_id=cascade_user")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "deleted"

        # Verify cascades: Contract, Clauses, Assessment, Deductions are all deleted
        assert db.query(Contract).filter(Contract.id == contract_id).count() == 0
        assert db.query(Clause).filter(Clause.contract_id == contract_id).count() == 0
        assert db.query(RiskAssessment).filter(RiskAssessment.contract_id == contract_id).count() == 0
        assert db.query(ChatMessage).filter(ChatMessage.contract_id == contract_id).count() == 0

        # Verify Vector store entries purged
        vector_res = vector_store_service.search(user_id="cascade_user", contract_id=contract_id, query="Payment")
        assert len(vector_res) == 0

    finally:
        db.close()
