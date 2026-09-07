# LegalLens ⚖️

> **AI-Powered Contract Intelligence Platform**  
> *Academic MCA Mini Project*

LegalLens provides an automated, explainable first-pass contract review and grounded conversational question-answering for everyday agreements (freelance, employment, rental, and vendor contracts).

> **Disclaimer**: LegalLens is a first-pass review tool designed to highlight risk points and answer clause-specific questions. It is **not** a substitute for professional legal counsel.

---

## Features
- 📄 **Multi-Format Ingestion**: Ingests PDF and DOCX files, extracting text while preserving structural section hierarchy and rejecting scanned/empty files.
- 🔍 **Clause Segmentation**: Splits documents into discrete, numbered clauses.
- 🏷️ **Clause Classification**: Classifies clauses into 15 core legal categories using fine-tuned InLegalBERT.
- ⚠️ **Explainable Risk Assessment**:
  - Imbalance heuristic rules (unilateral termination, uncapped indemnity, excessive non-competes).
  - Standard protective clause omission checklists for Employment, Freelance, Rental, and Vendor agreements.
  - Transparent weighted-deduction risk scoring model.
- 💬 **Grounded Q&A (RAG)**: Semantic search over clause embeddings (Sentence-Transformers + ChromaDB) with answers strictly citing source clauses.
- 📊 **Interactive Dashboard**: Modern React + Tailwind interface with risk gauges, clause breakdown, interactive chat, and exportable PDF summaries.
- 🔒 **Per-User Isolation**: Contracts and queries are strictly scoped to the authenticated user account.

---

## Tech Stack
- **Backend**: FastAPI, Python 3.10+, SQLAlchemy, PostgreSQL (psycopg2)
- **Document Parsing**: PyMuPDF, python-docx
- **NLP / ML**: Hugging Face Transformers, InLegalBERT, Sentence-Transformers, ChromaDB
- **Frontend**: React (Vite), Tailwind CSS
- **Evaluation**: Custom evaluation harness measuring Classification Macro-F1, Risk Flag Accuracy, QA citation correctness, and jurisdictional transfer to Indian contracts.

---

## Quick Start

### 1. Backend Setup
```bash
# Navigate to backend and create virtual environment
python -m venv venv
venv\Scripts\activate   # On Windows
# source venv/bin/activate  # On Unix

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL and LLM API keys
# For docker-free local PostgreSQL setup instructions, see docs/postgres_setup.md

# Run migrations and start backend server
uvicorn backend.app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Project Structure
```
legallens/
  backend/
    app/            # FastAPI app: routers, services, schemas
    ml/              # classification + risk scoring + embedding/retrieval code
    tests/          # automated unit and integration tests
  frontend/
    src/            # React dashboard components and state
  notebooks/
    finetune_inlegalbert_cuad.ipynb   # Colab-ready training notebook
  data/
    README.md        # CUAD dataset fetching instructions
  eval/
    results/        # Benchmark metrics and evaluation reports
  docs/
    architecture.md # System architecture documentation
  AGENTS.md         # Constitution & binding specifications
  README.md
```
