"""
Canonical LegalLens Clause Categories Definition.
Single source of truth for the 15 core commercial legal categories.
Derived from CUAD and defined in AGENTS.md / SRS specifications.
"""

from typing import List

CATEGORIES: List[str] = [
    "Termination",
    "Indemnification",
    "Limitation_of_Liability",
    "Confidentiality",
    "Non_Compete",
    "Governing_Law",
    "Dispute_Resolution",
    "Intellectual_Property",
    "Payment_Terms",
    "Term_and_Renewal",
    "Warranties",
    "Exclusivity_and_Non_Solicit",
    "Severability",
    "Force_Majeure",
    "Assignment",
]
