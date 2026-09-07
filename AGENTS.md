# LegalLens — Project Constitution

## Scope discipline
This is a single-developer, ~3-month MCA academic mini project, not an
enterprise product. Prefer the simplest thing that satisfies the SRS below
over anything "production-grade." Do not introduce Docker/K8s, microservice
splits, multi-cloud, message queues, or paid infrastructure unless a phase
explicitly asks for it. If you're ever choosing between "impressive" and
"matches the spec," choose the spec.

## Fixed technology stack (do not substitute without asking)
- Backend: Python 3.10+, FastAPI, Uvicorn
- Frontend: React (Vite), Tailwind CSS
- Database: PostgreSQL, accessed via SQLAlchemy (psycopg2 driver)
- Document parsing: PyMuPDF (PDF), python-docx (DOCX)
- Classification model: InLegalBERT, fine-tuned via HuggingFace
  Transformers + Datasets on the CUAD dataset
- Embeddings: Sentence-Transformers; vector store: ChromaDB or FAISS
  (pick one, document why, don't run both)
- RAG answer generation: external LLM API (Claude or GPT) called
  server-side only; API key from environment variable, never committed,
  never sent to the frontend
- Version control: Git, with meaningful incremental commits per module

## Repo layout (create this shape in Phase 0)
```
legallens/
  backend/
    app/            # FastAPI app: routers, services, schemas
    ml/              # classification + risk scoring + embedding/retrieval code
    tests/
  frontend/
    src/
  notebooks/
    finetune_inlegalbert_cuad.ipynb   # Colab-ready
  data/
    README.md        # where CUAD lives / how to fetch it, gitignored raw data
  eval/
    results/
  docs/
    architecture.md
  AGENTS.md
  README.md
```

## Non-negotiables
- Every risk flag must reference the specific clause id and rule/signal
  that produced it. No unexplained numeric scores.
- Every QA answer must cite the clause(s) it was grounded in, or explicitly
  say the contract doesn't address the question.
- Documents and analysis results are scoped per user account — never
  return one user's contract data to another.
- No LLM/API keys or DB credentials in source control; use `.env` +
  `.env.example`.
- The product is a first-pass review tool. Every user-facing surface that
  shows a risk score or answer must carry a visible "not legal advice"
  disclaimer.

## Non-goals for this project
- No support for jurisdictions/contract types beyond what's listed in the
  functional requirements.
- No multi-tenant billing, no admin console, no mobile app.
- No attempt to beat the literature's benchmark numbers — the evaluation
  harness exists to produce honest, reproducible numbers for the report,
  not to be tuned toward a target.

## When something in a phase prompt is ambiguous
State the assumption you're making in the walkthrough and proceed with the
most literal reading of the SRS language above — don't silently expand
scope to "do it properly."
