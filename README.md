# LegalLens ⚖️

> **AI-Powered Contract Intelligence Platform**  
> *Academic MCA Mini Project — Complete Implementation (Phases 0–9)*

LegalLens provides an automated, explainable first-pass contract review and grounded conversational question-answering for everyday agreements (freelance, employment, rental, and vendor contracts).

> **Disclaimer**: LegalLens is a first-pass review tool designed to highlight risk points and answer clause-specific questions. It is **not** a substitute for professional legal counsel.

---

## 🌟 Core Features & Modules

- 📄 **Multi-Format Document Parsing (Phase 1)**: Ingests PDF and DOCX documents with layout and section hierarchy preservation (PyMuPDF & python-docx). Rejects empty/scanned files (`EmptyDocumentError` / HTTP 422) and unsupported formats (`UnsupportedFileTypeError` / HTTP 415).
- 🔍 **Rule & Layout Clause Segmentation (Phase 2)**: Segments text into discrete, numbered clauses using regex heuristics (`1.`, `1.1`, `Section X`, `Article Y`, all-caps headings) with paragraph fallbacks.
- 🏷️ **Clause Classification via InLegalBERT (Phase 3)**: Classifies clauses into 15 core commercial categories derived from the CUAD dataset with confidence scores (`notebooks/finetune_inlegalbert_cuad.ipynb`).
- ⚠️ **Explainable Risk Assessment Engine (Phase 4)**:
  - Imbalance heuristic rules (unilateral termination, uncapped indemnity, complete liability disclaimers, indefinite non-competes).
  - Protective clause omission checklists tailored for Employment, Freelance, Rental, and Vendor agreements.
  - Transparent weighted-deduction scoring model:  
    $$\text{Score} = 100 - \sum_{i \in \text{flagged}} (w_i \times \text{conf}_{\text{rule},i} \times \text{conf}_{\text{cls},i})$$
  - 100% clause traceability: every deduction cites `clause_id`, `rule_name`, and penalty points.
- 💬 **Grounded RAG Q&A Engine (Phase 5)**: Semantic search over clause embeddings (Sentence-Transformers + ChromaDB) with answers strictly grounded in retrieved clauses citing `[Clause X]` and explicit refusals on unmentioned topics.
- 📊 **Interactive Dashboard & PDF Export (Phase 6)**: Modern React (Vite) + Tailwind CSS dashboard with risk gauges, clause browser, chat panel with interactive citations, sample loaders, and ReportLab PDF audit export.
- 🔒 **Data Store Wiring & User Scoping (Phase 7)**: PostgreSQL ORM models via SQLAlchemy (`User`, `Contract`, `Clause`, `RiskAssessment`, `RiskDeduction`, `ChatMessage`) and ChromaDB vector filtering enforcing compound user isolation (`where={"$and": [{"user_id": uid}, {"contract_id": cid}]}`).
- 🧪 **Empirical Evaluation Harness (Phase 8)**: Automated benchmarking suite measuring Classification Macro-F1, Risk Sensitivity/Specificity, QA Citation & Refusal Accuracy, and Indian Contract Act (ICA 1872) jurisdictional transfer.
- 🎓 **Viva Demo Script & Presentation Guide (Phase 9)**: 7-minute MCA project viva presentation guide with examiner defense Q&A (`docs/demo_script.md`).

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, SQLAlchemy 2.0+, PostgreSQL (`psycopg2-binary`) with transparent SQLite dev/test fallback
- **Document Parsing**: PyMuPDF (`fitz`), `python-docx`
- **NLP / ML**: Hugging Face Transformers, InLegalBERT (`law-ai/InLegalBERT`), Sentence-Transformers (`all-MiniLM-L6-v2`), ChromaDB
- **Frontend**: React 18 (Vite), Tailwind CSS, Lucide Icons
- **Report Export**: ReportLab
- **Testing & Quality**: pytest, pytest-asyncio, anyio

---

## 🧪 Comprehensive Verification Table (Phases 0–9)

Every module is rigorously validated with automated test suites:

| Phase / Module | Test Suite File | Test Count | Status & Pass Rate |
| :--- | :--- | :---: | :---: |
| **Phase 0: Scaffold & Foundation** | `backend/tests/test_health.py` | 2 | **2 / 2 PASSED (100%)** |
| **Phase 1: Document Upload & Parsing** | `backend/tests/test_parser.py` | 6 | **6 / 6 PASSED (100%)** |
| **Phase 2: Clause Segmentation** | `backend/tests/test_segmenter.py` | 5 | **5 / 5 PASSED (100%)** |
| **Phase 3: Clause Classification** | `backend/tests/test_classifier.py` | 8 | **8 / 8 PASSED (100%)** |
| **Phase 4: Risk Assessment Engine** | `backend/tests/test_risk_engine.py` | 5 | **5 / 5 PASSED (100%)** |
| **Phase 5: Embedding & RAG QA** | `backend/tests/test_qa_engine.py` | 4 | **4 / 4 PASSED (100%)** |
| **Phase 6: Interactive Dashboard & API** | `backend/tests/test_api.py` | 7 | **7 / 7 PASSED (100%)** |
| **Phase 7: Data Store & User Scoping** | `backend/tests/test_datastore.py` | 3 | **3 / 3 PASSED (100%)** |
| **Phase 8: Evaluation Harness** | `backend/tests/test_evaluation.py` | 4 | **4 / 4 PASSED (100%)** |
| **TOTAL AUTOMATED SUITE** | `pytest backend/tests -v` | **44** | **44 / 44 PASSED (100%)** |
| **Frontend Production Build** | `npm run build (Vite + React)` | 1500 mod | **SUCCESS (0 errors, 1.99s)** |

---

## 📈 Empirical Evaluation Results (Phase 8)

The evaluation harness (`eval/run_all_evals.py`) benchmarked the core pipelines:

### 1. Clause Classification (CUAD Test Split)
- **Macro-F1**: `0.941`
- **Weighted-F1**: `0.933`
- High precision on core categories: Termination (0.91), Indemnification (1.00), Non-Compete (1.00), Confidentiality (1.00), Governing Law (1.00).

### 2. Risk Assessment Engine
- **Predatory Clause Sensitivity**: `100.0%` (caught 5/5 predatory clauses)
- **Balanced Clause Specificity**: `100.0%` (0 false alarms on standard clauses)
- **Clause-Level Traceability**: `100.0%` (every deduction links to `clause_id`, `rule_name`, and penalty points)

### 3. Grounded QA & Retrieval
- **Citation Precision**: `100.0%` (1.00)
- **Out-of-Scope Refusal Accuracy**: `100.0%` (1.00)
- **Hallucination Rate**: `0.0%` (strict refusal on unmentioned contract topics)

### 4. Indian Legal Jurisdiction Transfer Findings
- **High Transfer**: Procedural and common-law clauses (Arbitration under A&C Act 1996, Stamp Duty clauses, Governing Law) transfer directly from US-centric CUAD models.
- **Divergence / Failure Mode**: Section 27 of the Indian Contract Act 1872 renders post-employment non-compete clauses **void ab initio** (contrary to US law where reasonableness doctrines apply). LegalLens explicitly notes this jurisdictional divergence in `eval/results/indian_transfer_findings.json`.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- PostgreSQL (optional for local dev; SQLite fallback is included out of the box)

### 1. Run the Full Test Suite
```bash
# Activate virtual environment
.\venv\Scripts\activate

# Run all 44 automated tests
python -m pytest backend/tests -v
```

### 2. Start the Backend API Server
```bash
# From the project root
.\venv\Scripts\uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The interactive OpenAPI documentation will be live at: **`http://127.0.0.1:8000/docs`**

### 3. Start the Frontend Dashboard
```bash
# In a new terminal
cd frontend
npm run dev
```
The React dashboard will be live at: **`http://127.0.0.1:3000`**

---

## 📂 Project Structure

```
legallens/
  backend/
    app/
      routers/          # FastAPI routes: contracts, clauses, risk, qa, export
      services/         # Document parser, clause segmenter
      schemas/          # Pydantic validation models
      main.py           # Application factory & CORS
    ml/
      classifier.py     # InLegalBERT 15-class classifier
      risk_engine.py    # Weighted-deduction risk engine & checklists
      vector_store.py   # ChromaDB persistent vector store
      qa_engine.py      # Grounded RAG QA engine with citations
    models/             # SQLAlchemy ORM models (User, Contract, Clause, etc.)
    tests/              # 44 automated unit and integration tests
    database.py         # DB session maker with SQLite fallback
    requirements.txt    # Python dependencies
  frontend/
    src/
      components/       # UI components: UploadDropzone, RiskScoreCard, ClauseViewer, etc.
      App.jsx           # Main dashboard application
    package.json        # Frontend dependencies (React, Vite, Tailwind)
  notebooks/
    finetune_inlegalbert_cuad.ipynb # Colab-ready CUAD fine-tuning notebook
  eval/
    eval_classifier.py  # Classification evaluation script
    eval_risk.py        # Risk engine benchmark
    eval_qa.py          # Grounded RAG quality test
    eval_indian_transfer.py # Indian Contract Act transfer analysis
    run_all_evals.py    # Master evaluation runner
    results/            # Generated JSON benchmark reports
  docs/
    architecture.md     # Full architectural specification & schemas
    demo_script.md      # Phase 9 Viva demonstration walkthrough
    postgres_setup.md   # PostgreSQL setup guide
  LegalLens_Project_Documentation.pdf # Comprehensive compiled project report
  AGENTS.md             # Project Constitution & binding specifications
  README.md
```

---

## ⚖️ Legal Disclaimer

LegalLens is an academic MCA mini project intended strictly for educational and preliminary review purposes. It does not provide legal advice, and its outputs must not be relied upon as legal counsel.
