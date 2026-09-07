"""
Pydantic schemas for Document Analysis, Risk Reporting, and Grounded Q&A.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    contract_id: str
    question: str
    user_id: Optional[str] = "default_user"


class ChatResponse(BaseModel):
    question: str
    answer: str
    citations: List[int]
    retrieved_clauses: List[Dict[str, Any]]
    is_grounded: bool
    disclaimer: str


class DocumentUploadResponse(BaseModel):
    contract_id: str
    filename: str
    contract_type: str
    page_count: int
    total_characters: int
    clauses: List[Dict[str, Any]]
    risk_report: Dict[str, Any]
    disclaimer: str = "LegalLens is an automated first-pass contract analysis tool. It does not provide legal advice."
