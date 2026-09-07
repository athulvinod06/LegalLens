"""
Document Analysis, Risk Assessment, and Grounded Q&A Router for LegalLens (Phase 7).
Persists contracts, clauses, risk audits, and chat history into PostgreSQL via SQLAlchemy
with strict per-user account isolation and vector store scoping.
"""

import uuid
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Contract, Clause, RiskAssessment, RiskDeduction, ChatMessage
from backend.app.schemas.document import DocumentUploadResponse, ChatRequest, ChatResponse
from backend.app.services.parser import parse_document, EmptyDocumentError, UnsupportedFileTypeError
from backend.app.services.segmenter import segment_into_clauses
from backend.ml.classifier import classifier_service
from backend.ml.risk_engine import risk_engine_service
from backend.ml.vector_store import vector_store_service
from backend.ml.qa_engine import qa_engine_service
from backend.app.services.pdf_export import generate_contract_pdf_report

router = APIRouter(tags=["Documents"])

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


def get_or_create_user(db: Session, user_id: str) -> User:
    """Ensures a user record exists in PostgreSQL for strict foreign-key scoping."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(
            id=user_id,
            email=f"{user_id}@legallens.local",
            hashed_password="hashed_placeholder_pw",
            full_name=user_id.replace("_", " ").title(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def process_and_persist_contract(
    raw_text: str,
    filename: str,
    contract_type: str,
    user_id: str,
    db: Session,
) -> DocumentUploadResponse:
    """
    Parses, segments, classifies, evaluates risk, and persists contract entities
    into PostgreSQL and ChromaDB with strict per-user ownership.
    """
    user = get_or_create_user(db, user_id)
    contract_id = f"doc_{uuid.uuid4().hex[:10]}"

    # 1. Segment text into discrete clauses
    segmented = segment_into_clauses(raw_text)
    if not segmented:
        raise HTTPException(status_code=400, detail="Unable to extract discrete clauses from document.")

    # 2. Classify clauses into 15 core CUAD categories
    classified = classifier_service.classify_clauses(segmented)

    # 3. Evaluate Risk Engine
    risk_report = risk_engine_service.evaluate_contract(classified, contract_type=contract_type)

    # 4. Index in Vector Store with User & Contract Scoping
    vector_store_service.index_clauses(user_id=user.id, contract_id=contract_id, clauses=classified)

    # 5. Persist Relational Records via SQLAlchemy
    contract = Contract(
        id=contract_id,
        user_id=user.id,
        filename=filename,
        contract_type=contract_type,
        page_count=max(1, len(segmented) // 5),
        total_characters=len(raw_text),
    )
    db.add(contract)

    # Persist Clauses
    clause_orm_map = {}
    for c in classified:
        clause_row = Clause(
            contract_id=contract.id,
            clause_id=c.clause_id,
            clause_number=c.clause_number,
            title=c.title,
            text=c.text,
            category=c.category,
            confidence=c.confidence,
            is_core_category=c.is_core_category,
        )
        db.add(clause_row)
        clause_orm_map[c.clause_id] = clause_row

    # Flush so clause PKs are generated
    db.flush()

    # Persist Risk Assessment
    assessment = RiskAssessment(
        contract_id=contract.id,
        overall_score=risk_report.overall_score,
        risk_level=risk_report.risk_level,
        total_deductions=risk_report.total_deductions,
        flags_count=risk_report.flags_count,
        omissions=json.dumps(risk_report.omissions),
    )
    db.add(assessment)
    db.flush()

    # Persist Risk Deductions (with strict traceability: clause_id, rule_name, points_deducted)
    for f in risk_report.flags:
        clause_ref = clause_orm_map.get(f.clause_id) if f.clause_id else None
        deduction = RiskDeduction(
            assessment_id=assessment.id,
            clause_ref_id=clause_ref.id if clause_ref else None,
            clause_id=f.clause_id,
            flag_id=f.flag_id,
            rule_id=f.rule_id,
            rule_name=f.rule_name,
            category=f.category,
            severity=f.severity,
            weight=f.weight,
            rule_confidence=f.rule_confidence,
            classifier_confidence=f.classifier_confidence,
            points_deducted=f.deduction_points,
            explanation=f.explanation,
            recommendation=f.recommendation,
        )
        db.add(deduction)

    db.commit()

    # Convert to response payload
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
        page_count=contract.page_count,
        total_characters=contract.total_characters,
        clauses=clauses_data,
        risk_report=risk_report.model_dump(),
    )

    ANALYSIS_CACHE[contract_id] = response_data.model_dump()
    return response_data


# Upload endpoints (supporting both /api/upload and /api/documents/upload)
@router.post("/api/upload", response_model=DocumentUploadResponse)
@router.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    contract_type: str = Form("freelance"),
    user_id: str = Form("default_user"),
    db: Session = Depends(get_db),
):
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

    return process_and_persist_contract(
        raw_text=parsed_doc.text,
        filename=file.filename,
        contract_type=contract_type,
        user_id=user_id,
        db=db,
    )


@router.post("/api/documents/sample/{contract_type}", response_model=DocumentUploadResponse)
def load_sample_contract(contract_type: str, user_id: str = "default_user", db: Session = Depends(get_db)):
    ctype = contract_type.lower()
    if ctype not in SAMPLE_CONTRACTS:
        raise HTTPException(status_code=404, detail=f"Sample contract '{contract_type}' not found.")

    text = SAMPLE_CONTRACTS[ctype]
    filename = f"sample_{ctype}_agreement.pdf"
    return process_and_persist_contract(text, filename, ctype, user_id=user_id, db=db)


# Risk endpoint with strict user scoping
@router.get("/api/contract/{contract_id}/risk")
@router.get("/api/documents/{contract_id}/risk")
def get_contract_risk(
    contract_id: str,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db),
):
    """
    Fetches persisted risk assessment strictly scoped to user_id.
    """
    contract = db.query(Contract).filter(Contract.id == contract_id, Contract.user_id == user_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found or access denied.")

    assessment = contract.assessment
    if not assessment:
        raise HTTPException(status_code=404, detail="Risk assessment not found for this contract.")

    deductions = db.query(RiskDeduction).filter(RiskDeduction.assessment_id == assessment.id).all()
    flags_data = [
        {
            "flag_id": d.flag_id,
            "clause_id": d.clause_id,
            "rule_id": d.rule_id,
            "rule_name": d.rule_name,
            "category": d.category,
            "severity": d.severity,
            "weight": d.weight,
            "rule_confidence": d.rule_confidence,
            "classifier_confidence": d.classifier_confidence,
            "deduction_points": d.points_deducted,
            "explanation": d.explanation,
            "recommendation": d.recommendation,
        }
        for d in deductions
    ]

    try:
        omissions = json.loads(assessment.omissions) if assessment.omissions else []
    except Exception:
        omissions = assessment.omissions.split(",") if assessment.omissions else []

    return {
        "contract_id": contract.id,
        "filename": contract.filename,
        "overall_score": assessment.overall_score,
        "risk_level": assessment.risk_level,
        "total_deductions": assessment.total_deductions,
        "flags_count": assessment.flags_count,
        "flags": flags_data,
        "omissions": omissions,
        "disclaimer": "LegalLens is an automated first-pass contract analysis tool. Not legal advice."
    }


# Grounded Chat endpoint with persistence & user scoping
@router.post("/api/contract/{contract_id}/chat", response_model=ChatResponse)
@router.post("/api/documents/chat", response_model=ChatResponse)
def grounded_chat(
    req: ChatRequest,
    contract_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    target_contract_id = contract_id or req.contract_id
    user_id = req.user_id or "default_user"

    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Enforce relational user scoping
    contract = db.query(Contract).filter(Contract.id == target_contract_id, Contract.user_id == user_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found or access denied.")

    # Execute grounded RAG QA
    qa_result = qa_engine_service.answer_question(
        user_id=user_id,
        contract_id=target_contract_id,
        question=req.question.strip(),
    )

    # Persist ChatMessage record in PostgreSQL
    chat_rec = ChatMessage(
        contract_id=contract.id,
        user_id=user_id,
        question=req.question.strip(),
        answer=qa_result.answer,
        citations=json.dumps(qa_result.citations),
        is_grounded=qa_result.is_grounded,
    )
    db.add(chat_rec)
    db.commit()

    return ChatResponse(
        question=qa_result.question,
        answer=qa_result.answer,
        citations=qa_result.citations,
        retrieved_clauses=qa_result.retrieved_clauses,
        is_grounded=qa_result.is_grounded,
        disclaimer=qa_result.disclaimer,
    )


# Contract Deletion with Cascades & Vector Store Cleanup
@router.delete("/api/contract/{contract_id}")
@router.delete("/api/documents/{contract_id}")
def delete_contract(
    contract_id: str,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db),
):
    """
    Deletes a contract, cascading deletion to all its clauses, assessments,
    deductions, and chat history, while purging vector embeddings.
    """
    contract = db.query(Contract).filter(Contract.id == contract_id, Contract.user_id == user_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found or access denied.")

    # 1. Purge vector embeddings
    vector_store_service.delete_contract_vectors(user_id=user_id, contract_id=contract_id)

    # 2. Delete relational contract (cascades to clauses, assessments, deductions, chat)
    db.delete(contract)
    db.commit()

    if contract_id in ANALYSIS_CACHE:
        del ANALYSIS_CACHE[contract_id]

    return {"status": "deleted", "contract_id": contract_id}


# PDF export endpoints
@router.post("/api/documents/export-pdf")
def export_pdf_report(analysis_data: Dict[str, Any]):
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


@router.get("/api/documents/{contract_id}/export-pdf")
def export_pdf_by_id(contract_id: str):
    if contract_id not in ANALYSIS_CACHE:
        raise HTTPException(status_code=404, detail="Contract ID not found in session cache.")
    return export_pdf_report(ANALYSIS_CACHE[contract_id])
