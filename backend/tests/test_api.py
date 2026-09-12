"""
API Integration tests for LegalLens endpoints (Phase 6).
"""

import io
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.tests.test_parser import create_sample_pdf, create_sample_docx

client = TestClient(app)


def test_api_load_sample_contract():
    """Verify loading and analyzing a pre-configured sample contract."""
    response = client.post("/api/documents/sample/freelance")
    assert response.status_code == 200
    data = response.json()
    assert data["contract_type"] == "freelance"
    assert "contract_id" in data
    assert len(data["clauses"]) >= 4
    assert "risk_report" in data
    assert data["risk_report"]["overall_score"] > 0
    assert "disclaimer" in data
    assert "classifier_source" in data
    assert data["classifier_source"] in ["baseline-keyword", "inlegalbert-cuad-finetuned"]


def test_api_upload_pdf():
    """Verify uploading and analyzing a real PDF via /api/documents/upload."""
    pdf_bytes = create_sample_pdf("""
    SOFTWARE DEVELOPMENT AGREEMENT
    1. Scope of Work: Contractor shall deliver backend FastAPI services.
    2. Payment: Client pays $8,000 upon completion within 15 days.
    3. Termination: Either party may cancel upon 30 days notice.
    4. Liability: Neither party is liable for punitive damages.
    """)
    response = client.post(
        "/api/documents/upload",
        files={"file": ("contract.pdf", pdf_bytes, "application/pdf")},
        data={"contract_type": "freelance", "user_id": "test_user_1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "contract.pdf"
    assert len(data["clauses"]) >= 4
    assert data["risk_report"]["risk_level"] in ["Low Risk", "Moderate Risk", "High Risk"]


def test_api_upload_empty_pdf_error():
    """Verify uploading an empty PDF returns 422 with clear error message."""
    pdf_bytes = create_sample_pdf("")
    response = client.post(
        "/api/documents/upload",
        files={"file": ("empty.pdf", pdf_bytes, "application/pdf")},
        data={"contract_type": "freelance"}
    )
    assert response.status_code == 422
    assert "no extractable text" in response.json()["detail"].lower()


def test_api_upload_unsupported_file_error():
    """Verify uploading an unsupported file format returns 415 error."""
    response = client.post(
        "/api/documents/upload",
        files={"file": ("agreement.txt", b"simple text", "text/plain")},
        data={"contract_type": "freelance"}
    )
    assert response.status_code == 415
    assert "unsupported file format" in response.json()["detail"].lower()


def test_api_grounded_chat():
    """Verify conversational Q&A endpoint returns grounded answers with citations."""
    # First load sample
    upload_resp = client.post("/api/documents/sample/freelance")
    contract_id = upload_resp.json()["contract_id"]

    # Ask relevant question
    chat_resp = client.post(
        "/api/documents/chat",
        json={
            "contract_id": contract_id,
            "question": "What is the termination notice period?",
            "user_id": "default_user",
        }
    )
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert data["is_grounded"] is True
    assert len(data["citations"]) > 0
    assert "14" in data["answer"] and "days" in data["answer"]
    assert "not legal advice" in data["disclaimer"].lower()


def test_api_chat_out_of_scope_refusal():
    """Verify chat endpoint strictly refuses out-of-scope question."""
    upload_resp = client.post("/api/documents/sample/freelance")
    contract_id = upload_resp.json()["contract_id"]

    chat_resp = client.post(
        "/api/documents/chat",
        json={
            "contract_id": contract_id,
            "question": "Are pets allowed in the office?",
            "user_id": "default_user",
        }
    )
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert data["is_grounded"] is False
    assert "does not address this question" in data["answer"].lower()


def test_api_export_pdf():
    """Verify PDF export endpoint generates a valid binary PDF document."""
    upload_resp = client.post("/api/documents/sample/freelance")
    contract_id = upload_resp.json()["contract_id"]

    pdf_resp = client.get(f"/api/documents/{contract_id}/export-pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000
    assert pdf_resp.content.startswith(b"%PDF")
