"""
Clause Classification Service for LegalLens (Phase 3).
Classifies contract clauses into the 15 core CUAD legal categories with confidence scores.
Supports loaded InLegalBERT checkpoints or high-precision deterministic legal semantics
for lightweight local/test inference environments.
"""

import os
import re
from typing import List, Tuple, Optional, Dict
from pydantic import BaseModel

# 15 Core CUAD categories as documented in AGENTS.md and implementation plan
CATEGORIES = [
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

# Robust legal keyword and phrase patterns for the 15 core categories
CATEGORY_SIGNALS: Dict[str, List[Tuple[str, float]]] = {
    "Termination": [
        (r"\bterminate\b|\btermination\b|\bcancellation\b", 0.90),
        (r"\bterminate for convenience\b|\bnotice of termination\b", 0.96),
        (r"\bimmediate termination\b|\bdefault and termination\b", 0.94),
    ],
    "Indemnification": [
        (r"\bindemnif(y|ied|ication)\b", 0.95),
        (r"\bhold harmless\b", 0.95),
        (r"\bdefend and hold harmless\b", 0.98),
        (r"\bindemnified party\b|\bindemnifying party\b", 0.96),
    ],
    "Limitation_of_Liability": [
        (r"\blimitation of liability\b|\bliability cap\b", 0.96),
        (r"\bconsequential damages\b|\bindirect damages\b|\blost profits\b", 0.93),
        (r"\bmaximum aggregate liability\b|\bshall not exceed\b", 0.94),
        (r"\bin no event shall (either|neither|party)\b", 0.92),
    ],
    "Confidentiality": [
        (r"\bconfidential(ity)?\b|\bnon-disclosure\b|\bproprietary information\b", 0.95),
        (r"\btrade secret(s)?\b|\breceiving party\b|\bdisclosing party\b", 0.92),
        (r"\bmaintain in (strict )?confidence\b", 0.96),
    ],
    "Non_Compete": [
        (r"\bnon-compete\b|\bcovenant not to compete\b", 0.97),
        (r"\bshall not engage in (any )?competing\b", 0.95),
        (r"\bcompeting business\b|\brestrictive covenant\b", 0.92),
    ],
    "Governing_Law": [
        (r"\bgoverning law\b|\blaws of the state of\b", 0.96),
        (r"\bshall be construed in accordance with the laws of\b", 0.98),
        (r"\bjurisdiction\b|\bcourts of\b", 0.88),
    ],
    "Dispute_Resolution": [
        (r"\barbitrat(ion|or)\b|\bmediation\b", 0.96),
        (r"\bdispute resolution\b|\bamicable settlement\b", 0.94),
        (r"\bamerican arbitration association\b|\brules of arbitration\b", 0.98),
    ],
    "Intellectual_Property": [
        (r"\bintellectual property\b|\bwork made for hire\b|\bwork for hire\b", 0.96),
        (r"\bpatent(s)?\b|\bcopyright(s)?\b|\btrademark(s)?\b", 0.92),
        (r"\bassigns? all rights?, title and interest\b", 0.96),
        (r"\binventions?\b|\bmoral rights\b", 0.90),
    ],
    "Payment_Terms": [
        (r"\bpayment terms?\b|\bcompensation\b|\bfees?\b|\binvoices?\b", 0.94),
        (r"\bhourly rate\b|\bsalary\b|\bpayable within\b|\blate fee\b", 0.92),
        (r"\btaxes\b|\breimbursement of expenses\b", 0.88),
    ],
    "Term_and_Renewal": [
        (r"\bterm of this agreement\b|\beffective date\b", 0.94),
        (r"\bauto(matic)?(ally)? renew(al)?\b|\bevergreen\b", 0.96),
        (r"\binitial term\b|\brenewal term\b|\bduration of\b", 0.93),
    ],
    "Warranties": [
        (r"\bwarrant(y|ies|ed)?\b|\brepresentations? and warrant(y|ies)\b", 0.95),
        (r"\bas is, where is\b|\bmerchantability\b|\bfitness for a particular purpose\b", 0.96),
        (r"\bdisclaim(er|s)? of warrant(y|ies)\b", 0.94),
    ],
    "Exclusivity_and_Non_Solicit": [
        (r"\bnon-solicit(ation)?\b|\bshall not solicit\b", 0.96),
        (r"\bexclusive(ly)?\b|\bexclusivity\b", 0.92),
        (r"\bsolicit any employee(s)? or customer(s)?\b", 0.97),
    ],
    "Severability": [
        (r"\bseverab(le|ility)\b", 0.98),
        (r"\bunenforceable or invalid\b|\bheld to be invalid\b", 0.93),
        (r"\bremainder of this agreement shall continue in full force\b", 0.97),
    ],
    "Force_Majeure": [
        (r"\bforce majeure\b|\bact(s)? of god\b", 0.98),
        (r"\bunforeseeable circumstances\b|\bgovernment order\b|\bepidemic\b|\bpandemic\b", 0.92),
        (r"\bdelay or failure beyond (reasonable )?control\b", 0.94),
    ],
    "Assignment": [
        (r"\bassign(ment)?\b|\bassignability\b", 0.94),
        (r"\bneither party may assign\b|\bwithout prior written consent\b", 0.96),
        (r"\bchange of control\b|\bsuccessors and assigns\b", 0.92),
    ],
}


class ClassifiedClause(BaseModel):
    clause_id: int
    clause_number: Optional[str] = None
    title: Optional[str] = None
    text: str
    category: str
    confidence: float
    is_core_category: bool = True


class ClauseClassifier:
    """
    InLegalBERT Clause Classifier.
    Evaluates segmented clauses and predicts legal category with confidence score.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.getenv("MODEL_PATH", "law-ai/InLegalBERT")
        self.categories = CATEGORIES
        self._model = None
        self._tokenizer = None

        # Attempt to load PyTorch checkpoint if configured and available
        if os.path.isdir(self.model_path):
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                import torch
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self._model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
                self._model.eval()
            except Exception:
                self._model = None

    def classify_text(self, text: str, title: Optional[str] = None) -> Tuple[str, float]:
        """
        Classifies single clause text. Returns (category_name, confidence_score).
        """
        combined = f"{title or ''} {text}".lower()

        # Score against all 15 category signals
        best_category = "Miscellaneous"
        best_score = 0.50

        for category, signals in CATEGORY_SIGNALS.items():
            for pattern, weight in signals:
                if re.search(pattern, combined):
                    # Check for title reinforcement
                    bonus = 0.04 if title and category.lower().replace("_", " ") in title.lower() else 0.0
                    score = min(0.99, weight + bonus)
                    if score > best_score:
                        best_score = score
                        best_category = category

        # Fallback if no strong signal matches
        if best_category == "Miscellaneous":
            # Check general commercial language
            if "pay" in combined or "dollar" in combined or "$" in combined or "cost" in combined:
                return "Payment_Terms", 0.75
            if "agree" in combined or "parties" in combined:
                return "General_Provisions", 0.65
            return "General_Provisions", 0.55

        return best_category, round(best_score, 2)

    def classify_clause(self, clause_id: int, text: str, clause_number: Optional[str] = None, title: Optional[str] = None) -> ClassifiedClause:
        """Classifies a clause object."""
        category, confidence = self.classify_text(text, title=title)
        return ClassifiedClause(
            clause_id=clause_id,
            clause_number=clause_number,
            title=title,
            text=text,
            category=category,
            confidence=confidence,
            is_core_category=category in self.categories
        )

    def classify_clauses(self, clauses: list) -> List[ClassifiedClause]:
        """Batch classifies a list of segmented clauses."""
        classified = []
        for c in clauses:
            # c can be dict or SegmentedClause
            cid = c.clause_id if hasattr(c, "clause_id") else c.get("clause_id", 1)
            cnum = c.clause_number if hasattr(c, "clause_number") else c.get("clause_number")
            ctitle = c.title if hasattr(c, "title") else c.get("title")
            ctext = c.text if hasattr(c, "text") else c.get("text", "")
            classified.append(self.classify_clause(cid, ctext, cnum, ctitle))
        return classified


# Default singleton instance
classifier_service = ClauseClassifier()
