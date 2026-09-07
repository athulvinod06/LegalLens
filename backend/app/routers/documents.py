"""
Document Analysis, Risk Assessment, and Grounded Q&A Router for LegalLens.
"""

import uuid
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from backend.app.schemas.document import DocumentUploadResponse, ChatRequest, ChatResponse
from backend.app.services.parser import parse_document, EmptyDocumentError, UnsupportedFileTypeError
from backend.app.services.segmenter import segment_into_clauses
from backend.ml.classifier import classifier_service
from backend.ml.risk_engine import risk_engine_service
from backend.ml.vector_store import vector_store_service
from backend.ml.qa_engine import qa_engine_service
from backend.app.services.pdf_export import generate_contract_pdf_report

router = APIRouter(prefix="/api/documents", tags=["Documents"])

# In-memory document storage cache for session persistence
ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}

SAMPLE_CONTRACTS = {
    "freelance": """
FREELANCE SERVICES AGREEMENT

1. Scope of Engagement
Contractor shall develop and deliver a full-stack responsive web application as specified in Schedule A.

2. Fees and Invoicing
Client agrees to pay Contractor a total fee of $12,000, payable 50% upfront and 50% upon final delivery.

3. Intellectual Property Assignment
Upon full receipt of payment, Contractor assigns all right, title, and interest in deliverables to Client.

4. Termination for Convenience
Either party may terminate this agreement at any time by giving fourteen (14) days prior written notice.

5. Limitation of Liability
In no event shall either party's aggregate liability exceed the total amounts paid under this Agreement.

6. Confidentiality Obligations
Each party agrees to maintain the confidentiality of all proprietary commercial information for 2 years.
    """,
    "employment": """
EMPLOYMENT AGREEMENT

1. Position and Scope
Employee shall serve as Senior Engineer and perform duties diligently.

2. Compensation and Salary
Employer shall pay an annual base salary of $110,000, payable in bi-weekly installments.

3. Termination
Company reserves the right to terminate Employee at any time without cause and with immediate effect.

4. Non-Compete Covenant
Employee shall not engage in any competing software business anywhere in the world for a period of three (3) years.

5. Governing Law and Arbitration
This Agreement is governed by the laws of Delaware. All disputes shall be resolved by binding arbitration.
    """,
    "rental": """
RESIDENTIAL LEASE AGREEMENT

1. Lease Term and Renewal
The initial term shall be 12 months commencing October 1, 2026, renewing month-to-month thereafter.

2. Monthly Rent and Security Deposit
Tenant shall pay $2,200 on the first day of each month, with a refundable security deposit of $2,200.

3. Termination Notice
Either Landlord or Tenant may terminate the tenancy at term end by providing thirty (30) days written notice.

4. Governing Law and Severability
This lease is governed by local tenancy laws. If any section is held invalid, the remainder remains in full effect.
    """,
    "vendor": """
MASTER VENDOR PROCUREMENT AGREEMENT

1. Supply of Goods and Warranties
Vendor warrants all delivered goods are new, free from defects, and conform strictly to specifications.

2. Invoicing and Payment Schedule
Payment is due within 45 days of receiving an undisputed invoice following acceptance.

3. Indemnification Clause
Vendor shall defend, indemnify, and hold harmless Buyer against any and all claims, liabilities, or losses whatsoever.

4. Force Majeure
Neither party is liable for failure to perform due to unforeseen disasters or acts of God beyond reasonable control.

5. Limitation of Liability
Buyer's total aggregate liability shall not exceed the amounts paid to Vendor in the preceding 6 months.
    """
}


def process_raw_contract_text(raw_text: str, filename: str, contract_type: str, user_id: str = "default_user") -> DocumentUploadResponse:
    """Internal helper to segment, classify, score, and vector-index contract text."""
    contract_id = f"doc_{uuid.uuid4().hex[:10]}"

    # 1. Segment text into discrete clauses
    segmented = segment_into_clauses(raw_text)
    if not segmented:
        raise HTTPException(status_code=400, detail="Unable to extract discrete clauses from document.")

    # 2. Classify clauses into 15 core CUAD categories
    classified = classifier_service.classify_clauses(segmented)

    # 3. Evaluate Risk Engine (heuristics, checklists, weighted deductions)
    risk_report = risk_engine_service.evaluate_contract(classified, contract_type=contract_type)

    # 4. Index in Vector Store for Grounded RAG QA
    vector_store_service.index_clauses(user_id=user_id, contract_id=contract_id, clauses=classified)

    # Convert classified clauses to serializable dicts
    clauses_data = [
        {
            "clause_id": c.clause_id,
            "clause_number": c.clause_number,
            "title": c.title,
            "text": c.text,
            "category": c.category,
            "confidence": c.confidence,
            "is_core_category": c.is_core_category,
        }
        for c in classified
    ]

    response_data = DocumentUploadResponse(
        contract_id=contract_id,
        filename=filename,
        contract_type=contract_type,
        page_count=max(1, len(segmented) // 5),
        total_characters=len(raw_text),
        clauses=clauses_data,
        risk_report=risk_report.model_dump(),
    )

    # Cache result for QA and PDF export
    ANALYSIS_CACHE[contract_id] = response_data.model_dump()
    return response_data


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    contract_type: str = Form("freelance"),
    user_id: str = Form("default_user"),
):
    """
    Upload and analyze a contract document (PDF or DOCX).
    Executes text extraction, clause segmentation, InLegalBERT classification,
    risk assessment scoring, and vector indexing.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

    try:
        parsed_doc = parse_document(file_bytes, file.filename)
    except EmptyDocumentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=415, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")

    return process_raw_contract_text(
        raw_text=parsed_doc.text,
        filename=file.filename,
        contract_type=contract_type,
        user_id=user_id,
    )


@router.post("/sample/{contract_type}", response_model=DocumentUploadResponse)
def load_sample_contract(contract_type: str, user_id: str = "default_user"):
    """
    Instantly loads and analyzes a pre-configured sample contract
    for testing: 'freelance', 'employment', 'rental', or 'vendor'.
    """
    ctype = contract_type.lower()
    if ctype not in SAMPLE_CONTRACTS:
        raise HTTPException(status_code=404, detail=f"Sample contract '{contract_type}' not found.")

    text = SAMPLE_CONTRACTS[ctype]
    filename = f"sample_{ctype}_agreement.pdf"
    return process_raw_contract_text(text, filename, ctype, user_id=user_id)


@router.post("/chat", response_model=ChatResponse)
def grounded_chat(req: ChatRequest):
    """
    Grounded conversational Q&A endpoint (RAG).
    Retrieves top clauses from the vector store and synthesizes answers
    with citations [Clause X]. Strictly refuses out-of-scope questions.
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    qa_result = qa_engine_service.answer_question(
        user_id=req.user_id or "default_user",
        contract_id=req.contract_id,
        question=req.question.strip(),
    )
    return ChatResponse(
        question=qa_result.question,
        answer=qa_result.answer,
        citations=qa_result.citations,
        retrieved_clauses=qa_result.retrieved_clauses,
        is_grounded=qa_result.is_grounded,
        disclaimer=qa_result.disclaimer,
    )


@router.post("/export-pdf")
def export_pdf_report(analysis_data: Dict[str, Any]):
    """
    Generates and downloads a branded PDF summary audit report.
    """
    try:
        pdf_bytes = generate_contract_pdf_report(analysis_data)
        filename = analysis_data.get("filename", "contract_review").replace(".pdf", "").replace(".docx", "")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=LegalLens_{filename}_Review.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")


@router.get("/{contract_id}/export-pdf")
def export_pdf_by_id(contract_id: str):
    """
    Exports PDF report for a cached contract ID.
    """
    if contract_id not in ANALYSIS_CACHE:
        raise HTTPException(status_code=404, detail="Contract ID not found in session cache.")
    return export_pdf_report(ANALYSIS_CACHE[contract_id])
