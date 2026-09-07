"""
Clause ORM model for LegalLens (Phase 7).
Persists segmented and classified clauses.
"""

import uuid
from sqlalchemy import Column, String, Integer, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Clause(Base):
    __tablename__ = "clauses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    clause_id = Column(Integer, nullable=False)  # 1-based sequential index within contract
    clause_number = Column(String(50), nullable=True)
    title = Column(String(255), nullable=True)
    text = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    is_core_category = Column(Boolean, default=True, nullable=False)

    # Scoped Relationships
    contract = relationship("Contract", back_populates="clauses")
    deductions = relationship("RiskDeduction", back_populates="clause")
