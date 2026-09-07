"""
Risk Assessment ORM model for LegalLens (Phase 7).
Persists overall contract score and checklist omissions.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    overall_score = Column(Float, nullable=False)
    risk_level = Column(String(50), nullable=False)
    total_deductions = Column(Float, default=0.0, nullable=False)
    flags_count = Column(Integer, default=0, nullable=False)
    omissions = Column(Text, nullable=True)  # JSON or comma-separated omissions
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Scoped Relationships
    contract = relationship("Contract", back_populates="assessment")
    deductions = relationship("RiskDeduction", back_populates="assessment", cascade="all, delete-orphan")
