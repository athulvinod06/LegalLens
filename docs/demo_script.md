# LegalLens — MCA Viva / Panel Demonstration Script

This walkthrough script is prepared for the MCA project viva / academic panel evaluation. It provides a structured 7-minute demonstration of the LegalLens architecture, algorithmic pipelines, explainable risk model, and grounded question-answering.

---

## Panel Walkthrough Timeline (7 Minutes)

### 1. Introduction & Motivation (Minute 0:00 – 1:00)
- **The Problem**: Individuals, freelancers, and small enterprises frequently sign legally binding contracts (employment bonds, freelance IP agreements, rental leases, vendor scopes) without legal counsel due to steep legal consultation fees.
- **The Pitfall of Generic AI**: Pasting contracts into general-purpose LLMs generates unstructured, ungrounded, and unauditable text that risks legal liability and hallucinations.
- **The Solution**: **LegalLens** provides an automated, structured, and explainable first-pass contract intelligence review — never a substitute for professional legal counsel, but an auditable first line of defense.
- **Constitution**: Built in strict adherence to `AGENTS.md` (no unnecessary enterprise bloat, zero black-box scoring, strict per-user account isolation, and prominent "Not Legal Advice" disclaimers).

---

### 2. Live System Architecture & Running State (Minute 1:00 – 2:00)
- **Show Running Services**:
  - Frontend: [http://localhost:3000](http://localhost:3000) (React + Vite + Tailwind CSS)
  - Backend API: [http://localhost:8000](http://localhost:8000) (FastAPI + Swagger Docs at `/docs`)
  - Relational Database: PostgreSQL accessed via SQLAlchemy 2.0+
  - Vector Store: ChromaDB with persistent metadata filtering
- **Point to Disclaimer Banner**:
  - Show the persistent amber notice at the top of the interface: *"LegalLens is an automated first-pass contract analysis tool. It does not provide legal advice."*

---

### 3. Pipeline 1: Document Upload, Segmentation & Classification (Minute 2:00 – 3:30)
- **Step 1: One-Click Demo / File Upload**:
  - Click the **"Sample Freelance"** or **"Sample Employment"** button (or drag-and-drop a PDF/DOCX contract).
  - Highlight the format validation: invalid file types (e.g. `.txt`) return HTTP 415; empty/scanned image-only PDFs return HTTP 422 (`EmptyDocumentError`).
- **Step 2: Clause Segmentation Engine**:
  - Show how the raw extracted text is segmented into discrete, numbered clauses using section regex (`1.`, `Section 2`, `Article III`) and paragraph boundaries.
- **Step 3: InLegalBERT CUAD Classification**:
  - Each clause is mapped to one of the **15 core CUAD legal categories** (Termination, Indemnification, Limitation of Liability, Confidentiality, Non-Compete, etc.) with calibrated confidence scores (e.g. `95% conf`).

---

### 4. Explainable Risk Assessment Engine (Minute 3:30 – 4:45)
- **Show Overall Score & Gauge**:
  - Display the overall risk score (e.g. `42/100 High Risk` on predatory contracts or `86/100 Low Risk` on fair contracts).
- **Explain the Mathematical Model**:
  $$\text{Score} = \max\left(0, 100 - \sum_{i \in \text{flagged}} (w_i \times \text{rule\_confidence}_i \times \text{classifier\_confidence}_i)\right)$$
  - *Key Academic Point*: Deliberately **not an average** across all clauses. An average dilutes a severe issue (like an uncapped indemnity or immediate unilateral termination) among standard boilerplate clauses.
- **Traceability Demonstration**:
  - Click on a flagged clause (e.g., *Unilateral Termination* or *Excessive Non-Compete*).
  - Show that every deduction references: `clause_id`, `rule_id` (`RULE_UNILATERAL_TERMINATION`), penalty points deducted (e.g. `-21.4 pts`), plain-language explanation, and practical remedy recommendation.
- **Checklist Audit**:
  - Show the **Missing Essential Protective Clauses** banner (e.g. missing Limitation of Liability or Payment Terms).

---

### 5. Pipeline 2: Grounded Conversational Q&A / RAG (Minute 4:45 – 5:45)
- **Step 1: In-Scope Grounded Question**:
  - Ask: *"How can this agreement be terminated and what is the notice period?"*
  - Show the response: The system retrieves the exact clause from the vector store and cites `[Clause 4: Termination for Convenience]`.
  - Click the citation badge `[Clause 4]` — watch the dashboard automatically scroll to and highlight Clause 4 in the clause explorer!
- **Step 2: Strict Anti-Hallucination Out-of-Scope Refusal**:
  - Ask: *"Does this contract permit keeping dogs or pets in the office?"*
  - Show the response: *"The contract does not address this question based on the retrieved clauses."*
  - Explain to the panel that the RAG pipeline is constrained against ungrounded speculation.

---

### 6. Relational Data Store & PDF Export (Minute 5:45 – 6:30)
- **User Scoping & Persistence**:
  - Point out that all contracts, clauses, risk deductions, and chat messages are persisted in PostgreSQL with strict foreign keys to `user_id`.
  - Mention automated test `test_user_isolation_security`, verifying User B cannot query or fetch User A's data or vector embeddings.
- **Export PDF Summary Report**:
  - Click **"Export PDF Audit"**.
  - Open the downloaded branded PDF showing the executive risk score, deduction breakdown, and clause inventory.

---

### 7. Evaluation Harness & Indian Jurisdictional Findings (Minute 6:30 – 7:00)
- **Show Benchmark Metrics**:
  - Run or cite `eval/results/evaluation_summary.md`:
    - Classification Macro-F1: `0.78`
    - Risk Flag Sensitivity: `100.0%`
    - QA Citation Accuracy: `100.0%`
    - QA Refusal Accuracy on Ungrounded Queries: `100.0%`
    - Traceability Rate: `100.0%`
- **Indian Jurisdictional Transfer Finding**:
  - Note the constitutional research finding: models trained on US CUAD struggle with Indian statutory nuances (e.g. post-employment non-competes being void ab initio under Section 27 of the Indian Contract Act 1872).
  - Documented as an academic finding on legal domain transfer.

---

## Viva Q&A Cheat Sheet

| Likely Panel Question | Concise Recommended Answer |
| :--- | :--- |
| **Why InLegalBERT over generic BERT?** | InLegalBERT is pre-trained specifically on legal corpora (Indian and common law court judgments), better understanding domain syntax and legalese semantics than general BERT. |
| **Why not average clause risk scores?** | Averaging would allow ten standard boilerplate clauses (e.g., notice addresses, severability) to dilute one lethal uncapped indemnity or unilateral termination clause. The weighted deduction model isolates and penalizes specific risks directly. |
| **How is hallucination prevented in RAG?** | The server-side prompt and similarity thresholds restrict answers strictly to retrieved clause context, explicitly forcing a standardized refusal statement when questions are ungrounded. |
| **How is data isolated between users?** | PostgreSQL enforces relational user scoping via `user_id` foreign keys, and ChromaDB vector queries enforce compound filters (`{"$and": [{"user_id": uid}, {"contract_id": cid}]}`). |
