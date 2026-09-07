# LegalLens System Architecture

## 1. System Overview
LegalLens is an AI-powered contract intelligence platform built as an academic MCA mini project. It provides explainable, first-pass automated contract review and grounded question-answering for freelance, employment, rental, and vendor agreements.

## 2. Core Pipelines
```
[User Document: PDF / DOCX]
       │
       ▼
[Document Parsing (PyMuPDF / python-docx)]
       │
       ▼
[Clause Segmentation (RegEx + Layout)]
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
[Clause Classification (InLegalBERT)]    [Embedding (Sentence-Transformers)]
       │                                         │
       ▼                                         ▼
[Risk Assessment Engine (Rules+Checklist)]  [ChromaDB Vector Store]
       │                                         │
       ▼                                         ▼
[PostgreSQL Relational DB]              [Grounded Q&A Engine (RAG)]
       │                                         │
       └──────────────────┬──────────────────────┘
                          ▼
           [FastAPI Web API (Uvicorn)]
                          │
                          ▼
        [React + Tailwind CSS Dashboard]
```

### Pipeline 1: Document Analysis Pipeline
1. **Upload & Parsing**: Accepts PDF or DOCX; validates that readable text is present. Malformed or purely image-based files are rejected with a clear user-facing error.
2. **Clause Segmentation**: Splits raw extracted text into coherent clause units using numbering patterns, section headers, and semantic boundaries.
3. **Clause Classification**: Classifies each clause into one of 15 core CUAD categories using InLegalBERT with confidence scores.
4. **Risk Assessment Engine**: Evaluates flagged clauses using rule-based heuristics and contract-type checklist omissions. Computes an explainable overall risk score using a weighted-deduction model:
   $$\text{Overall Score} = 100 - \sum_{\text{flagged}} (w_i \times \text{rule\_confidence}_i \times \text{classifier\_confidence}_i)$$

### Pipeline 2: Grounded Q&A (RAG)
1. **Clause Embeddings**: Generates embeddings via Sentence-Transformers and persists them to ChromaDB, indexed by `contract_id` and scoped by `user_id`.
2. **Retrieval**: User question is embedded and top matching clauses are retrieved with similarity scores.
3. **Grounded Answer Generation**: External LLM (server-side only) synthesizes an answer grounded strictly on retrieved clauses, providing citations `[Clause X]`, and refusing to hallucinate when clauses do not address the prompt.

## 3. Technology Stack
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, PostgreSQL (psycopg2)
- **Frontend**: React (Vite), Tailwind CSS, Lucide Icons
- **ML & NLP**:
  - InLegalBERT (`law-ai/InLegalBERT`) fine-tuned on CUAD
  - Sentence-Transformers (`all-MiniLM-L6-v2`)
  - Vector Store: ChromaDB
- **Document Processing**: PyMuPDF (`fitz`), `python-docx`
- **Report Generation**: ReportLab (PDF export)

## 4. Security & Compliance
- **Account Isolation**: Contracts, extracted clauses, embeddings, and chat histories are strictly scoped by `user_id`.
- **Credential Protection**: API keys and DB credentials loaded via environment variables; never committed or sent to client.
- **Auditable Scorer**: No unexplained risk scores. Every flag references clause text, rule identifier, and confidence.
- **Legal Disclaimer**: A prominent "Not Legal Advice" disclaimer is present on all risk assessment views and exports.
