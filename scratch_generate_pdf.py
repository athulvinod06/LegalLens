import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 11 * inch - 36, "LegalLens — AI-Powered Contract Intelligence Platform")
            self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "Project Documentation")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 54, 36, page_text)
        disclaimer_text = "LegalLens | MCA Academic Mini Project | First-pass review | Not Legal Advice"
        self.drawString(54, 36, disclaimer_text)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 46, 8.5 * inch - 54, 46)
        self.restoreState()

def build_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    primary_color = colors.HexColor("#0f172a") # Slate 900
    accent_color = colors.HexColor("#2563eb")  # Blue 600
    subtle_color = colors.HexColor("#475569")  # Slate 600
    bg_light = colors.HexColor("#f8fafc")      # Slate 50
    border_color = colors.HexColor("#e2e8f0")  # Slate 200

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=subtle_color,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=accent_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#78350f")
    )

    story = []

    # Title Block
    story.append(Paragraph("LegalLens — Project Documentation & Progress", title_style))
    story.append(Paragraph("AI-Powered Contract Intelligence Platform &bull; Academic MCA Mini Project", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceBefore=0, spaceAfter=12))

    # Mandatory Legal Notice Callout
    callout_data = [[
        Paragraph("<b>IMPORTANT NOTICE / DISCLAIMER:</b> LegalLens is designed as an automated first-pass contract analysis tool for academic evaluation. It highlights risk indicators and enables grounded Q&A. It does not provide legal advice and is never a substitute for a licensed attorney.", callout_style)
    ]]
    callout_table = Table(callout_data, colWidths=[504])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fffbeb")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#fde68a")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 10))

    # Section 1: Executive Summary & Problem
    story.append(Paragraph("1. Executive Summary & Problem Statement", h1_style))
    story.append(Paragraph(
        "Individuals, freelancers, and small businesses routinely execute contracts (employment agreements, freelance deliverables, rental leases, vendor scopes) without legal counsel due to high hourly legal fees and complex legalese. Generic AI chatbots provide unstructured, ungrounded, and unauditable text that risks legal exposure. "
        "<b>LegalLens</b> provides a fast, structured, explainable first-pass contract review coupled with grounded conversational question-answering strictly citing source clauses.",
        body_style
    ))

    # Section 2: Architectural Constitution (AGENTS.md)
    story.append(Paragraph("2. Project Constitution & Scope Discipline", h1_style))
    story.append(Paragraph(
        "Development is strictly governed by <b>AGENTS.md</b> (the project constitution). Per its directives:",
        body_style
    ))
    story.append(Paragraph("&bull; <b>Scope Discipline:</b> Built as an MCA mini project. Avoids Docker, Kubernetes, microservice splits, distributed message queues, or paid multi-cloud tiers. Prioritizes specification adherence over superficial enterprise complexity.", bullet_style))
    story.append(Paragraph("&bull; <b>Clause-Level Traceability:</b> Every risk flag and risk score deduction must reference the specific clause ID and heuristic rule. Black-box or unexplained scores are prohibited.", bullet_style))
    story.append(Paragraph("&bull; <b>Strict Grounded Q&A:</b> Every answer must cite the specific retrieved clause(s) or explicitly state that the contract does not address the question.", bullet_style))
    story.append(Paragraph("&bull; <b>User Account Isolation:</b> All documents, clauses, embeddings, and chat histories are scoped by user account.", bullet_style))
    story.append(Paragraph("&bull; <b>Security:</b> No API keys or credentials committed; managed strictly via <code>.env</code> and <code>.env.example</code>.", bullet_style))

    # Section 3: Technology Stack
    story.append(Paragraph("3. Fixed Technology Stack", h1_style))
    tech_data = [
        [Paragraph("<b>Component</b>", body_style), Paragraph("<b>Technology Selected</b>", body_style), Paragraph("<b>Rationale & Details</b>", body_style)],
        [Paragraph("Backend Framework", body_style), Paragraph("FastAPI, Uvicorn, Python 3.10+", body_style), Paragraph("High performance, native async, automatic OpenAPI docs.", body_style)],
        [Paragraph("Frontend UI", body_style), Paragraph("React (Vite), Tailwind CSS", body_style), Paragraph("Modern, responsive dashboard, fast development cycle.", body_style)],
        [Paragraph("Database", body_style), Paragraph("PostgreSQL via SQLAlchemy (psycopg2)", body_style), Paragraph("Relational integrity for users, contracts, clauses, and risk reports.", body_style)],
        [Paragraph("Document Parsing", body_style), Paragraph("PyMuPDF (fitz) & python-docx", body_style), Paragraph("High-fidelity structural extraction for PDF and DOCX files.", body_style)],
        [Paragraph("Clause Classifier", body_style), Paragraph("InLegalBERT (law-ai/InLegalBERT)", body_style), Paragraph("Specialized legal language model fine-tuned on CUAD dataset.", body_style)],
        [Paragraph("Vector Store & RAG", body_style), Paragraph("Sentence-Transformers + ChromaDB", body_style), Paragraph("Local embedded persistent vector database with native metadata filtering.", body_style)],
        [Paragraph("Grounded LLM", body_style), Paragraph("External LLM API (Server-side)", body_style), Paragraph("Server-side calls only; protected API keys, strict citation rules.", body_style)],
    ]
    t_tech = Table(tech_data, colWidths=[110, 150, 244])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 10))

    # Section 4: 15 Core CUAD Categories
    story.append(Paragraph("4. Core 15 CUAD Classification Categories", h1_style))
    story.append(Paragraph(
        "From the 41 CUAD legal categories, the 15 most consequential for commercial and civil contracts were selected and mapped:",
        body_style
    ))
    cat_data = [
        [Paragraph("1. Termination", body_style), Paragraph("6. Governing Law", body_style), Paragraph("11. Warranties", body_style)],
        [Paragraph("2. Indemnification", body_style), Paragraph("7. Dispute Resolution", body_style), Paragraph("12. Exclusivity / Non-Solicit", body_style)],
        [Paragraph("3. Limitation of Liability", body_style), Paragraph("8. Intellectual Property", body_style), Paragraph("13. Severability", body_style)],
        [Paragraph("4. Confidentiality / NDA", body_style), Paragraph("9. Payment Terms", body_style), Paragraph("14. Force Majeure", body_style)],
        [Paragraph("5. Non-Compete", body_style), Paragraph("10. Term and Renewal", body_style), Paragraph("15. Assignment & Change of Control", body_style)],
    ]
    t_cat = Table(cat_data, colWidths=[168, 168, 168])
    t_cat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_cat)
    story.append(Spacer(1, 10))

    # Section 5: Risk Engine & Formula
    story.append(Paragraph("5. Explainable Risk Assessment Engine", h1_style))
    story.append(Paragraph(
        "Rather than computing an uninterpretable average across all clauses (which dangerously dilutes severe issues), LegalLens employs an explainable <b>weighted-deduction model</b>:",
        body_style
    ))
    story.append(Paragraph(
        "<b>Overall Risk Score:</b> <i>Score = 100 - &sum;<sub>i &isin; flagged</sub> (Weight<sub>i</sub> &times; Confidence<sub>rule,i</sub> &times; Confidence<sub>classifier,i</sub>)</i>",
        body_style
    ))
    story.append(Paragraph("&bull; <b>Imbalance Heuristics:</b> Flags unilateral termination for convenience, uncapped indemnification, complete liability disclaimers, and indefinite non-competes.", bullet_style))
    story.append(Paragraph("&bull; <b>Checklist Omission Audit:</b> Tailored checklists for Employment, Freelance, Rental, and Vendor agreements flag missing critical protections.", bullet_style))
    story.append(Paragraph("&bull; <b>Auditability:</b> Every penalty points directly to clause index, triggering rule, penalty points deducted, and layman explanation.", bullet_style))

    # Section 6: Accomplishments in Phase 0
    story.append(Paragraph("6. Phase 0 Implementation & Verification Status", h1_style))
    status_data = [
        [Paragraph("<b>Milestone / Deliverable</b>", body_style), Paragraph("<b>Artifact / Path</b>", body_style), Paragraph("<b>Status / Verification</b>", body_style)],
        [Paragraph("Canonical Repo Layout", body_style), Paragraph("<code>backend/, frontend/, notebooks/, eval/, docs/</code>", body_style), Paragraph("✅ Verified matching AGENTS.md", body_style)],
        [Paragraph("Security & Config", body_style), Paragraph("<code>.gitignore, .env.example, .env</code>", body_style), Paragraph("✅ Verified credentials untracked", body_style)],
        [Paragraph("Python Environment", body_style), Paragraph("<code>venv/, requirements.txt</code>", body_style), Paragraph("✅ Verified dependencies isolated", body_style)],
        [Paragraph("Postgres Setup Guide", body_style), Paragraph("<code>docs/postgres_setup.md</code>", body_style), Paragraph("✅ Docker-free Windows/macOS/Linux guide", body_style)],
        [Paragraph("FastAPI Health Stub", body_style), Paragraph("<code>backend/app/main.py</code>", body_style), Paragraph("✅ /health and /api/health responding", body_style)],
        [Paragraph("Automated Tests", body_style), Paragraph("<code>backend/tests/test_health.py</code>", body_style), Paragraph("✅ 2/2 pytest passing (0.33s)", body_style)],
        [Paragraph("Frontend Scaffold", body_style), Paragraph("<code>frontend/ (Vite + React + Tailwind)</code>", body_style), Paragraph("✅ vite build (1.52s), Dev server 200 OK", body_style)],
        [Paragraph("Fine-Tuning Notebook", body_style), Paragraph("<code>notebooks/finetune_inlegalbert_cuad.ipynb</code>", body_style), Paragraph("✅ Colab-ready InLegalBERT pipeline", body_style)],
        [Paragraph("Local Running State", body_style), Paragraph("<code>http://localhost:3000</code> & <code>:8000</code>", body_style), Paragraph("✅ Both services successfully running", body_style)],
    ]
    t_stat = Table(status_data, colWidths=[130, 200, 174])
    t_stat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_stat)
    story.append(Spacer(1, 10))

    # Section 7: Master Roadmap
    story.append(Paragraph("7. Master 10-Phase Project Roadmap", h1_style))
    roadmap_data = [
        [Paragraph("<b>Phase</b>", body_style), Paragraph("<b>Title</b>", body_style), Paragraph("<b>Key Scope & Deliverables</b>", body_style)],
        [Paragraph("Phase 0", body_style), Paragraph("Scaffold & Verification", body_style), Paragraph("<b>[COMPLETED]</b> Layout, venv, requirements, Vite/React skeleton, health test, running servers.", body_style)],
        [Paragraph("Phase 1", body_style), Paragraph("Document Upload & Parsing", body_style), Paragraph("PDF (PyMuPDF) & DOCX extraction, structure preservation, rejection of empty/scanned files.", body_style)],
        [Paragraph("Phase 2", body_style), Paragraph("Clause Segmentation", body_style), Paragraph("Heading/numbering/paragraph-based clause splitting, test with sample contracts.", body_style)],
        [Paragraph("Phase 3", body_style), Paragraph("Clause Classification", body_style), Paragraph("CUAD InLegalBERT Colab notebook & inference service for 15 core categories.", body_style)],
        [Paragraph("Phase 4", body_style), Paragraph("Risk Assessment Engine", body_style), Paragraph("Checklists, imbalance heuristics, weighted deduction model, clause traceability.", body_style)],
        [Paragraph("Phase 5", body_style), Paragraph("Embedding & RAG QA", body_style), Paragraph("ChromaDB vector store, Sentence-Transformers embeddings, grounded QA with citations.", body_style)],
        [Paragraph("Phase 6", body_style), Paragraph("Interactive Dashboard", body_style), Paragraph("React dashboard, upload flow, risk view, chat panel, PDF summary export, browser screenshots.", body_style)],
        [Paragraph("Phase 7", body_style), Paragraph("Data Store Wiring", body_style), Paragraph("PostgreSQL persistence with per-user scoping across tables and vector store.", body_style)],
        [Paragraph("Phase 8", body_style), Paragraph("Evaluation Harness", body_style), Paragraph("Precision/recall/macro-F1 on CUAD, risk accuracy, QA quality, Indian contract transfer.", body_style)],
        [Paragraph("Phase 9", body_style), Paragraph("Polish & Docs", body_style), Paragraph("Final docs, architecture diagrams, viva demo walkthrough script.", body_style)],
    ]
    t_road = Table(roadmap_data, colWidths=[64, 150, 290])
    t_road.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_road)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Successfully generated PDF report at: {filename}")

if __name__ == "__main__":
    out_file = os.path.abspath("LegalLens_Project_Documentation.pdf")
    build_pdf(out_file)
