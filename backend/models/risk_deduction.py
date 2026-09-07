"""
Risk Deduction ORM model for LegalLens (Phase 7).
Persists traceable risk flags and penalties.
"""

import uuid
from sqlalchemy import Column, String, Float, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from backend.database import Base


class RiskDeduction(Base):
    __tablename__ = "risk_deductions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(String(36), ForeignKey("risk_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    clause_ref_id = Column(String(36), ForeignKey("clauses.id", ondelete="SET NULL"), nullable=True, index=True)
    clause_id = Column(Integer, nullable=True)  # Clause index for direct reference and prompt requirement
    flag_id = Column(String(50), nullable=False)
    rule_id = Column(String(100), nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    weight = Column(Float, nullable=False)
    rule_confidence = Column(Float, nullable=False)
    classifier_confidence = Column(Float, nullable=False)
    points_deducted = Column(Float, nullable=False)  # Traceable deduction points
    explanation = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)

    # Scoped Relationships
    assessment = relationship("RiskAssessment", back_populates="deductions")
    clause = relationship("Clause", back_populates="deductions")
