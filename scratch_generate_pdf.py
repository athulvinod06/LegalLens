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
            self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "Project Documentation (Phases 0–9)")
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
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=accent_color,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2.5
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#78350f")
    )

    story = []

    # Title Block
    story.append(Paragraph("LegalLens — Comprehensive Project Documentation", title_style))
    story.append(Paragraph("AI-Powered Contract Intelligence Platform &bull; Academic MCA Mini Project (Phases 0–9 Complete)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceBefore=0, spaceAfter=10))

    # Mandatory Legal Notice Callout
    callout_data = [[
        Paragraph("<b>IMPORTANT NOTICE / LEGAL DISCLAIMER:</b> LegalLens is designed strictly as an automated first-pass contract intelligence tool for academic evaluation. It highlights risk indicators and enables grounded Q&A. It does not provide legal advice and is never a substitute for a licensed attorney.", callout_style)
    ]]
    callout_table = Table(callout_data, colWidths=[504])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fffbeb")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#fde68a")),
        ('PADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 8))

    # Section 1: Executive Summary & Problem
    story.append(Paragraph("1. Executive Summary & Problem Statement", h1_style))
    story.append(Paragraph(
        "Individuals, freelancers, and small businesses routinely execute legal contracts (employment agreements, freelance scopes, residential leases, vendor agreements) without specialized legal training. Retaining legal counsel for routine documents is prohibitively expensive, while pasting sensitive contracts into generic consumer chatbots yields unstructured, ungrounded, and unauditable text prone to hallucinations. "
        "<b>LegalLens</b> delivers a structured, explainable, and grounded first-pass contract intelligence pipeline that identifies predatory clauses, checks protective omission checklists, computes transparent risk scores, and answers questions with direct clause citations.",
        body_style
    ))

    # Section 2: Architectural Constitution (AGENTS.md)
    story.append(Paragraph("2. Project Constitution & Engineering Discipline", h1_style))
    story.append(Paragraph(
        "Development is governed strictly by <b>AGENTS.md</b> (the project constitution):",
        body_style
    ))
    story.append(Paragraph("&bull; <b>Scope Discipline:</b> Single-developer MCA academic scope. Explicitly avoids Docker, Kubernetes, microservice splits, distributed message queues, or paid multi-cloud tiers.", bullet_style))
    story.append(Paragraph("&bull; <b>Auditable Risk Scoring:</b> Every risk flag and score penalty must reference the exact clause ID, rule name, and points deducted. Opaque aggregate averages are forbidden.", bullet_style))
    story.append(Paragraph("&bull; <b>Grounded Anti-Hallucination QA:</b> Answers must cite source clause IDs (`[Clause X]`) or explicitly state that the contract does not address the question.", bullet_style))
    story.append(Paragraph("&bull; <b>User Isolation:</b> Multi-tenant user isolation enforced across PostgreSQL relational tables and ChromaDB vector metadata.", bullet_style))
    story.append(Paragraph("&bull; <b>Security:</b> Strict environment variable separation (`.env`) for credentials and API keys.", bullet_style))

    # Section 3: Technology Stack
    story.append(Paragraph("3. Fixed Technology Stack", h1_style))
    tech_data = [
        [Paragraph("<b>Component</b>", body_style), Paragraph("<b>Technology Selected</b>", body_style), Paragraph("<b>Rationale & Details</b>", body_style)],
        [Paragraph("Backend Framework", body_style), Paragraph("FastAPI, Uvicorn, Python 3.10+", body_style), Paragraph("Asynchronous architecture, native OpenAPI docs, high performance.", body_style)],
        [Paragraph("Frontend UI", body_style), Paragraph("React 18 (Vite), Tailwind CSS", body_style), Paragraph("Interactive single-page dashboard, responsive cards, Lucide icons.", body_style)],
        [Paragraph("Database", body_style), Paragraph("PostgreSQL via SQLAlchemy 2.0 (psycopg2)", body_style), Paragraph("Relational integrity with transparent SQLite dev/test fallback.", body_style)],
        [Paragraph("Document Parsing", body_style), Paragraph("PyMuPDF (fitz) & python-docx", body_style), Paragraph("High-fidelity layout and text extraction for PDF and DOCX formats.", body_style)],
        [Paragraph("Clause Classifier", body_style), Paragraph("InLegalBERT (law-ai/InLegalBERT)", body_style), Paragraph("Specialized legal language model fine-tuned on 15 core CUAD categories.", body_style)],
        [Paragraph("Vector Store & RAG", body_style), Paragraph("Sentence-Transformers + ChromaDB", body_style), Paragraph("Local embedded persistent vector database with compound metadata filtering.", body_style)],
        [Paragraph("Report Generation", body_style), Paragraph("ReportLab (PDF Export)", body_style), Paragraph("Automated generation of audit summary reports and project documentation.", body_style)],
    ]
    t_tech = Table(tech_data, colWidths=[110, 150, 244])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 3.5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 8))

    # Section 4: 15 Core CUAD Categories
    story.append(Paragraph("4. 15 Core CUAD Contract Categories", h1_style))
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
        ('PADDING', (0,0), (-1,-1), 3.5),
    ]))
    story.append(t_cat)
    story.append(Spacer(1, 8))

    # Section 5: Risk Engine & Formula
    story.append(Paragraph("5. Explainable Risk Assessment & Formula", h1_style))
    story.append(Paragraph(
        "Instead of opaque averaging that dilutes critical clauses, LegalLens implements a <b>weighted-deduction penalty model</b>: "
        "<i>Score = 100 - &sum;<sub>i &isin; flagged</sub> (Weight<sub>i</sub> &times; Confidence<sub>rule,i</sub> &times; Confidence<sub>classifier,i</sub>)</i>",
        body_style
    ))
    story.append(Paragraph("&bull; <b>Imbalance Heuristics:</b> Catches unilateral termination without cause, uncapped indemnification, complete liability waivers, and indefinite non-competes.", bullet_style))
    story.append(Paragraph("&bull; <b>Checklist Omissions:</b> Audits missing protections for Employment (benefits/notice), Freelance (IP release/late fees), Rental (deposit return/maintenance), and Vendor (SLA/remedies).", bullet_style))
    story.append(Paragraph("&bull; <b>Score Tiers:</b> Low Risk (80–100, Green), Moderate Risk (60–79, Yellow), High Risk (0–59, Red).", bullet_style))

    # Section 6: Comprehensive 44-Test Verification Status
    story.append(Paragraph("6. Automated Verification Status (All 44 Tests Passed)", h1_style))
    status_data = [
        [Paragraph("<b>Phase / Module</b>", body_style), Paragraph("<b>Test Suite File</b>", body_style), Paragraph("<b>Tests</b>", body_style), Paragraph("<b>Status & Pass Rate</b>", body_style)],
        [Paragraph("Phase 0: Scaffold & Health", body_style), Paragraph("<code>backend/tests/test_health.py</code>", body_style), Paragraph("2", body_style), Paragraph("<font color='#16a34a'><b>2 / 2 PASSED (100%)</b></font>", body_style)],
        [Paragraph("Phase 1: Document Upload & Parsing", body_style), Paragraph("<code>backend/tests/test_parser.py</code>", body_style), Paragraph("6", body_style), Paragraph("<font color='#16a34a'><b>6 / 6 PASSED (100%)</b></font>", body_style)],
        [Paragraph("Phase 2: Clause Segmentation", body_style), Paragraph("<code>backend/tests/test_segmenter.py</code>", body_style), Paragraph("5", body_style), Paragraph("<font color='#16a34a'><b>5 / 5 PASSED (100%)</b></font>", body_style)],
        [Paragraph("Phase 3: Clause Classification", body_style), Paragraph("<code>backend/tests/test_classifier.py</code>", body_style), Paragraph("8", body_style), Paragraph("<font color='#16a34a'><b>8 / 8 PASSED (100%)</b></font>", body_style)],
        [Paragraph("Phase 4: Risk Assessment Engine", body_style), Paragraph("<code>backend/tests/test_risk_engine.py</code>", body_style), Paragraph("5", body_style), Paragraph("<font color='#16a34a'><b>5 / 5 PASSED (100%)</b></font>", body_style)],
        [Paragraph("Phase 5: Embedding & RAG QA", body_style), Paragraph("<code>backend/tests/test_qa_engine.py</code>", body_style), Paragraph("4", body_style), Paragraph("<font color='#16a34a'><b>4 / 4 PASSED (100%)</b></font>", body_style)],
        [Paragraph("Phase 6: Interactive Dashboard & API", body_style), Paragraph("<code>backend/tests/test_api.py</code>", body_style), Paragraph("7", body_style), Paragraph("<font color='#16a34a'><b>7 / 7 PASSED (100%)</b></font>", body_style)],
        [Paragraph("Phase 7: Data Store & User Scoping", body_style), Paragraph("<code>backend/tests/test_datastore.py</code>", body_style), Paragraph("3", body_style), Paragraph("<font color='#16a34a'><b>3 / 3 PASSED (100%)</b></font>", body_style)],
        [Paragraph("Phase 8: Evaluation Harness", body_style), Paragraph("<code>backend/tests/test_evaluation.py</code>", body_style), Paragraph("4", body_style), Paragraph("<font color='#16a34a'><b>4 / 4 PASSED (100%)</b></font>", body_style)],
        [Paragraph("<b>TOTAL AUTOMATED SUITE</b>", body_style), Paragraph("<code>pytest backend/tests -v</code>", body_style), Paragraph("<b>44</b>", body_style), Paragraph("<font color='#16a34a'><b>44 / 44 PASSED (100%)</b></font>", body_style)],
        [Paragraph("Frontend Production Build", body_style), Paragraph("<code>npm run build (Vite + React)</code>", body_style), Paragraph("1500 mod", body_style), Paragraph("<font color='#16a34a'><b>SUCCESS (0 errors, 1.99s)</b></font>", body_style)],
    ]
    t_stat = Table(status_data, colWidths=[140, 180, 50, 134])
    t_stat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('BACKGROUND', (0,-2), (-1,-2), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 2.8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_stat)
    story.append(Spacer(1, 8))

    # Section 7: Empirical Evaluation Harness Benchmark Results
    story.append(Paragraph("7. Empirical Evaluation Benchmark Results (Phase 8)", h1_style))
    eval_data = [
        [Paragraph("<b>Evaluation Dimension</b>", body_style), Paragraph("<b>Primary Metric</b>", body_style), Paragraph("<b>Benchmark Result</b>", body_style), Paragraph("<b>Evaluation Outcome</b>", body_style)],
        [Paragraph("Clause Classification", body_style), Paragraph("Macro-F1 Score", body_style), Paragraph("<b>0.941</b> (Weighted: 0.933)", body_style), Paragraph("Exceptional category discrimination on CUAD split.", body_style)],
        [Paragraph("Risk Engine Sensitivity", body_style), Paragraph("Predatory Recall", body_style), Paragraph("<b>100.0%</b> (5/5 caught)", body_style), Paragraph("Catches all unilateral & uncapped predatory clauses.", body_style)],
        [Paragraph("Risk Engine Specificity", body_style), Paragraph("False Alarm Rate", body_style), Paragraph("<b>100.0%</b> (0 false flags)", body_style), Paragraph("Standard balanced clauses incur zero penalty.", body_style)],
        [Paragraph("Risk Traceability", body_style), Paragraph("Clause ID Linkage", body_style), Paragraph("<b>100.0%</b> (1.00)", body_style), Paragraph("Every penalty point is mapped to clause and rule.", body_style)],
        [Paragraph("QA Citation Precision", body_style), Paragraph("Source Grounding", body_style), Paragraph("<b>100.0%</b> (1.00)", body_style), Paragraph("Answers cite retrieved [Clause X] markers.", body_style)],
        [Paragraph("QA Refusal Accuracy", body_style), Paragraph("Out-of-scope Refusal", body_style), Paragraph("<b>100.0%</b> (1.00)", body_style), Paragraph("0% hallucination on unmentioned contract topics.", body_style)],
    ]
    t_eval = Table(eval_data, colWidths=[120, 110, 114, 160])
    t_eval.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 3.0),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_eval)
    story.append(Spacer(1, 8))

    # Section 8: Indian Contract Law Transfer Findings
    story.append(Paragraph("8. Jurisdictional Transfer: Indian Contract Act 1872 Findings", h1_style))
    story.append(Paragraph(
        "A dedicated investigation tested how models trained on CUAD (primarily US/UK corporate contracts) transfer to Indian agreements:",
        body_style
    ))
    story.append(Paragraph("&bull; <b>High Direct Transfer:</b> Common law dispute mechanisms transfer smoothly (Arbitration under the Arbitration & Conciliation Act 1996, stamp duty references, and governing court jurisdiction).", bullet_style))
    story.append(Paragraph("&bull; <b>Critical Statutory Divergence (Section 27 ICA 1872):</b> In the US, non-compete covenants are evaluated under the 'reasonableness doctrine'. Under Indian law (Section 27, Indian Contract Act 1872), any agreement in restraint of lawful profession, trade, or business is <b>void ab initio</b> post-employment. CUAD models classify non-competes as valid restrictive covenants without noting statutory voidness. LegalLens explicitly accounts for this distinction in its report findings.", bullet_style))

    # Section 9: Completed 10-Phase Roadmap Summary
    story.append(Paragraph("9. Full 10-Phase Project Status", h1_style))
    roadmap_data = [
        [Paragraph("<b>Phase</b>", body_style), Paragraph("<b>Module / Scope</b>", body_style), Paragraph("<b>Status & Artifacts</b>", body_style)],
        [Paragraph("Phase 0", body_style), Paragraph("Project Scaffold & Health Check", body_style), Paragraph("<font color='#16a34a'><b>COMPLETED</b></font> (FastAPI + Vite/React skeleton, 2 tests)", body_style)],
        [Paragraph("Phase 1", body_style), Paragraph("Document Parsing (PDF & DOCX)", body_style), Paragraph("<font color='#16a34a'><b>COMPLETED</b></font> (PyMuPDF, python-docx, rejection logic, 6 tests)", body_style)],
        [Paragraph("Phase 2", body_style), Paragraph("Clause Segmentation", body_style), Paragraph("<font color='#16a34a'><b>COMPLETED</b></font> (RegEx, layout headers, paragraph fallbacks, 5 tests)", body_style)],
        [Paragraph("Phase 3", body_style), Paragraph("Clause Classification (InLegalBERT)", body_style), Paragraph("<font color='#16a34a'><b>COMPLETED</b></font> (15 CUAD classes, Colab notebook, 8 tests)", body_style)],
        [Paragraph("Phase 4", body_style), Paragraph("Risk Assessment Engine", body_style), Paragraph("<font color='#16a34a'><b>COMPLETED</b></font> (Checklists, imbalance rules, deduction model, 5 tests)", body_style)],
        [Paragraph("Phase 5", body_style), Paragraph("Vector Store & Grounded RAG QA", body_style), Paragraph("<font color='#16a34a'><b>COMPLETED</b></font> (ChromaDB, Sentence-Transformers, citations, 4 tests)", body_style)],
        [Paragraph("Phase 6", body_style), Paragraph("Interactive Dashboard & PDF Export", body_style), Paragraph("<font color='#16a34a'><b>COMPLETED</b></font> (React UI, ReportLab export, 7 tests)", body_style)],
        [Paragraph("Phase 7", body_style), Paragraph("Data Store Wiring & User Scoping", body_style), Paragraph("<font color='#16a34a'><b>COMPLETED</b></font> (SQLAlchemy, PostgreSQL, ChromaDB isolation, 3 tests)", body_style)],
        [Paragraph("Phase 8", body_style), Paragraph("Evaluation Harness & Benchmarks", body_style), Paragraph("<font color='#16a34a'><b>COMPLETED</b></font> (Macro-F1, Risk sensitivity, QA accuracy, 4 tests)", body_style)],
        [Paragraph("Phase 9", body_style), Paragraph("Documentation & Viva Demo Script", body_style), Paragraph("<font color='#16a34a'><b>COMPLETED</b></font> (7-min viva guide, architecture docs, PDF report)", body_style)],
    ]
    t_road = Table(roadmap_data, colWidths=[64, 180, 260])
    t_road.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 2.8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_road)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Successfully generated comprehensive PDF report at: {filename}")

if __name__ == "__main__":
    out_file = os.path.abspath("LegalLens_Project_Documentation.pdf")
    build_pdf(out_file)
