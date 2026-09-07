"""
SQLAlchemy ORM models package for LegalLens.
"""

from backend.models.user import User
from backend.models.contract import Contract
from backend.models.clause import Clause
from backend.models.risk_assessment import RiskAssessment
from backend.models.risk_deduction import RiskDeduction
from backend.models.chat_message import ChatMessage

__all__ = [
    "User",
    "Contract",
    "Clause",
    "RiskAssessment",
    "RiskDeduction",
    "ChatMessage",
]
