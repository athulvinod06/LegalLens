"""
Risk Assessment Engine for LegalLens (Phase 4).
Evaluates classified contract clauses using an explainable weighted-deduction model,
protective checklist omission audits, and imbalance/extremity heuristics.
Every flag strictly references clause_id, rule_id, penalty points, and plain-language rationale.
"""

import re
from typing import List, Optional, Dict
from pydantic import BaseModel
from backend.ml.classifier import ClassifiedClause

# Checklists of essential protective clauses per contract type
CONTRACT_CHECKLISTS: Dict[str, Dict[str, float]] = {
    "employment": {
        "Termination": 15.0,
        "Payment_Terms": 15.0,
        "Dispute_Resolution": 10.0,
        "Confidentiality": 10.0,
        "Governing_Law": 10.0,
    },
    "freelance": {
        "Payment_Terms": 18.0,
        "Intellectual_Property": 18.0,
        "Termination": 12.0,
        "Limitation_of_Liability": 12.0,
    },
    "rental": {
        "Payment_Terms": 18.0,
        "Term_and_Renewal": 15.0,
        "Termination": 15.0,
        "Governing_Law": 12.0,
    },
    "vendor": {
        "Payment_Terms": 15.0,
        "Limitation_of_Liability": 15.0,
        "Indemnification": 15.0,
        "Termination": 12.0,
        "Force_Majeure": 8.0,
    },
}

# Heuristic rules for clause imbalance and extremity
IMBALANCE_RULES = [
    {
        "rule_id": "RULE_UNILATERAL_TERMINATION",
        "rule_name": "Unilateral Termination for Convenience",
        "category": "Termination",
        "severity": "HIGH",
        "weight": 25.0,
        "pattern": r"(sole discretion|at its option|without cause|at any time).{0,60}(terminate|cancel)|(company|employer|client)\s+may\s+terminate.{0,50}without\s+(notice|cause)",
        "explanation": "Allows one party to terminate the contract immediately without mutual rights or reasonable notice.",
        "recommendation": "Require mutual termination rights with a minimum 30-day prior written notice period.",
    },
    {
        "rule_id": "RULE_UNCAPPED_INDEMNIFICATION",
        "rule_name": "Broad Uncapped Indemnification",
        "category": "Indemnification",
        "severity": "HIGH",
        "weight": 25.0,
        "pattern": r"(defend,\s*indemnify|hold harmless).{0,70}(any and all|all claims|whatsoever|unlimited|indirect)",
        "explanation": "Imposes broad, uncapped liability to indemnify against third-party claims without fault boundaries.",
        "recommendation": "Cap indemnification obligations to gross negligence or willful misconduct, subject to the overall liability cap.",
    },
    {
        "rule_id": "RULE_TOTAL_LIABILITY_DISCLAIMER",
        "rule_name": "Disproportionate Liability Waiver",
        "category": "Limitation_of_Liability",
        "severity": "HIGH",
        "weight": 20.0,
        "pattern": r"(in no event shall|under no circumstances shall).{0,50}(company|client|employer).{0,50}(liable for any|any damages)",
        "explanation": "One-sided waiver of liability protecting only one party from damages.",
        "recommendation": "Make limitation of liability mutual and ensure remedies exist for breach of confidentiality and payment.",
    },
    {
        "rule_id": "RULE_EXCESSIVE_NON_COMPETE",
        "rule_name": "Excessive Non-Compete Scope/Duration",
        "category": "Non_Compete",
        "severity": "HIGH",
        "weight": 22.0,
        "pattern": r"(for a period of|within)\s+(\d{1,2}|two|three|five)\s+years|worldwide|anywhere in the world",
        "explanation": "Restricts livelihood for an excessive duration (over 12 months) or unrealistic geographic scope.",
        "recommendation": "Reduce duration to 6-12 months max and restrict geographic territory to relevant active markets.",
    },
    {
        "rule_id": "RULE_EXORBITANT_LATE_FEE",
        "rule_name": "Unreasonable Payment Penalty",
        "category": "Payment_Terms",
        "severity": "MEDIUM",
        "weight": 14.0,
        "pattern": r"(interest of|late fee of)\s+(\d{2}%|[2-9]% per month|forfeit|penalty)",
        "explanation": "Specifies aggressive interest or fee penalties that exceed standard commercial rates.",
        "recommendation": "Align late interest rates to standard statutory commercial rates (e.g. 1-1.5% per month or statutory bank rate).",
    },
    {
        "rule_id": "RULE_UNILATERAL_MODIFICATION",
        "rule_name": "Unilateral Contract Amendment",
        "category": "General_Provisions",
        "severity": "MEDIUM",
        "weight": 15.0,
        "pattern": r"(reserves the right to modify|amend this agreement at any time|in its sole discretion)",
        "explanation": "Grants one party the power to unilaterally alter contract terms without mutual consent.",
        "recommendation": "Require that all amendments or variations be made in writing and signed by both parties.",
    },
    {
        "rule_id": "RULE_PERPETUAL_CONFIDENTIALITY",
        "rule_name": "Indefinite Confidentiality Term",
        "category": "Confidentiality",
        "severity": "LOW",
        "weight": 8.0,
        "pattern": r"(in perpetuity|perpetual|indefinitely|forever)",
        "explanation": "Obligates non-disclosure indefinitely for all commercial information rather than standard 2-5 year terms.",
        "recommendation": "Limit non-disclosure to 2-3 years post-termination, preserving perpetual protection only for true trade secrets.",
    },
]


class RiskFlag(BaseModel):
    flag_id: str
    clause_id: Optional[int] = None
    clause_number: Optional[str] = None
    clause_snippet: Optional[str] = None
    rule_id: str
    rule_name: str
    category: str
    severity: str  # HIGH, MEDIUM, LOW
    weight: float
    rule_confidence: float
    classifier_confidence: float
    deduction_points: float
    explanation: str
    recommendation: str


class RiskAssessmentReport(BaseModel):
    overall_score: float  # 0 to 100
    risk_level: str       # "Low Risk", "Moderate Risk", "High Risk"
    total_deductions: float
    flags_count: int
    flags: List[RiskFlag]
    omissions: List[str]
    disclaimer: str = (
        "LegalLens is an automated first-pass contract analysis tool. "
        "Every risk score deduction is explainable and traceable to specific clauses and rules. "
        "This assessment does not constitute legal advice."
    )


class RiskAssessmentEngine:
    """
    Hybrid Risk Assessment Engine for LegalLens.
    Calculates explainable weighted-deduction risk scores and checks protective checklists.
    """

    def __init__(self):
        self.rules = IMBALANCE_RULES
        self.checklists = CONTRACT_CHECKLISTS

    def evaluate_contract(
        self,
        classified_clauses: List[ClassifiedClause],
        contract_type: str = "freelance"
    ) -> RiskAssessmentReport:
        """
        Runs full risk assessment across clauses and returns an explainable report.
        """
        contract_type = contract_type.lower().strip()
        if contract_type not in self.checklists:
            contract_type = "freelance"

        flags: List[RiskFlag] = []
        flag_counter = 1

        # 1. Evaluate Heuristic Rules against each clause
        for clause in classified_clauses:
            text_lower = clause.text.lower()
            for rule in self.rules:
                match = re.search(rule["pattern"], text_lower, re.IGNORECASE)
                if match:
                    rule_conf = 0.90
                    cls_conf = clause.confidence
                    weight = rule["weight"]
                    # Weighted deduction formula: weight * rule_conf * cls_conf
                    deduction = round(weight * rule_conf * cls_conf, 1)

                    snippet = clause.text[:140] + "..." if len(clause.text) > 140 else clause.text
                    flags.append(
                        RiskFlag(
                            flag_id=f"FLAG_{flag_counter:03d}",
                            clause_id=clause.clause_id,
                            clause_number=clause.clause_number,
                            clause_snippet=snippet,
                            rule_id=rule["rule_id"],
                            rule_name=rule["rule_name"],
                            category=clause.category,
                            severity=rule["severity"],
                            weight=weight,
                            rule_confidence=rule_conf,
                            classifier_confidence=cls_conf,
                            deduction_points=deduction,
                            explanation=rule["explanation"],
                            recommendation=rule["recommendation"],
                        )
                    )
                    flag_counter += 1

        # 2. Check Protective Checklist Omissions
        present_categories = {c.category for c in classified_clauses}
        omissions: List[str] = []
        required_items = self.checklists.get(contract_type, {})

        for req_cat, penalty in required_items.items():
            if req_cat not in present_categories:
                omissions.append(req_cat)
                deduction = round(penalty * 0.90, 1)
                cat_clean = req_cat.replace('_', ' ')
                flags.append(
                    RiskFlag(
                        flag_id=f"FLAG_{flag_counter:03d}",
                        clause_id=None,
                        clause_number=None,
                        clause_snippet=None,
                        rule_id=f"OMISSION_{req_cat.upper()}",
                        rule_name=f"Missing Protective Clause: {cat_clean}",
                        category=req_cat,
                        severity="MEDIUM" if penalty <= 12.0 else "HIGH",
                        weight=penalty,
                        rule_confidence=0.90,
                        classifier_confidence=1.0,
                        deduction_points=deduction,
                        explanation=(
                            f"This {contract_type.capitalize()} contract lacks a standard '{cat_clean}' clause, "
                            f"leaving key rights and protections undefined."
                        ),
                        recommendation=f"Add a clear, standard '{cat_clean}' provision.",
                    )
                )
                flag_counter += 1

        # 3. Compute Overall Weighted Score: 100 - sum(deductions)
        total_deductions = sum(f.deduction_points for f in flags)
        raw_score = 100.0 - total_deductions
        final_score = max(0.0, min(100.0, round(raw_score, 1)))

        # 4. Determine Risk Band
        if final_score >= 80.0:
            risk_level = "Low Risk"
        elif final_score >= 50.0:
            risk_level = "Moderate Risk"
        else:
            risk_level = "High Risk"

        return RiskAssessmentReport(
            overall_score=final_score,
            risk_level=risk_level,
            total_deductions=round(total_deductions, 1),
            flags_count=len(flags),
            flags=flags,
            omissions=omissions,
        )


# Default singleton instance
risk_engine_service = RiskAssessmentEngine()
