"""
PDF Summary Report Generation Service for LegalLens (Phase 6).
Generates a downloadable, branded PDF audit summary report using ReportLab.
"""

import io
from typing import Dict, Any, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfgen import canvas


class ReportNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(ReportNumberedCanvas, self).__init__(*args, **kwargs)
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

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 11 * inch - 36, "LegalLens — Contract Audit Summary")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

        # Running Footer
        self.drawRightString(8.5 * inch - 54, 36, f"Page {self._pageNumber} of {page_count}")
        self.drawString(54, 36, "LegalLens | Automated First-Pass Review | Not Legal Advice")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 46, 8.5 * inch - 54, 46)
        self.restoreState()


def generate_contract_pdf_report(analysis_data: Dict[str, Any]) -> bytes:
    """
    Builds a PDF report summarizing contract analysis results.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    primary = colors.HexColor("#0f172a")
    blue = colors.HexColor("#2563eb")
    border_color = colors.HexColor("#e2e8f0")

    title_style = ParagraphStyle(
        'RepTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=primary, spaceAfter=4
    )
    sub_style = ParagraphStyle(
        'RepSub', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor("#64748b"), spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'RepH2', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=blue, spaceBefore=12, spaceAfter=6
    )
    body_style = ParagraphStyle(
        'RepBody', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=13, textColor=primary
    )
    callout_style = ParagraphStyle(
        'RepCallout', parent=styles['Normal'],
        fontName='Helvetica-Oblique', fontSize=8.5, leading=12, textColor=colors.HexColor("#92400e")
    )

    story = []

    # Title & Metadata
    filename = analysis_data.get("filename", "Contract")
    contract_type = analysis_data.get("contract_type", "General").capitalize()
    overall_score = analysis_data.get("risk_report", {}).get("overall_score", 100.0)
    risk_level = analysis_data.get("risk_report", {}).get("risk_level", "Low Risk")

    story.append(Paragraph(f"LegalLens — Contract Review Report: {filename}", title_style))
    story.append(Paragraph(f"Agreement Type: <b>{contract_type}</b> &bull; Overall Score: <b>{overall_score}/100 ({risk_level})</b>", sub_style))

    # Mandatory Legal Notice Banner
    notice_data = [[Paragraph(
        "<b>LEGAL DISCLAIMER:</b> This report was generated automatically by LegalLens for informational and first-pass review purposes. "
        "It does not constitute legal advice. Please consult a qualified legal professional before signing.", callout_style
    )]]
    notice_table = Table(notice_data, colWidths=[504])
    notice_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef3c7")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#f59e0b")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(notice_table)
    story.append(Spacer(1, 10))

    # Executive Risk Summary Table
    story.append(Paragraph("1. Executive Risk Summary", h2_style))
    flags = analysis_data.get("risk_report", {}).get("flags", [])
    omissions = analysis_data.get("risk_report", {}).get("omissions", [])

    summary_rows = [
        [Paragraph("<b>Metric</b>", body_style), Paragraph("<b>Value</b>", body_style), Paragraph("<b>Assessment</b>", body_style)],
        [Paragraph("Overall Risk Score", body_style), Paragraph(f"<b>{overall_score} / 100</b>", body_style), Paragraph(f"<b>{risk_level}</b>", body_style)],
        [Paragraph("Identified Risk Flags", body_style), Paragraph(str(len(flags)), body_style), Paragraph("Issues requiring renegotiation or attention", body_style)],
        [Paragraph("Missing Standard Clauses", body_style), Paragraph(str(len(omissions)), body_style), Paragraph(", ".join(omissions) if omissions else "None (Checklist Complete)", body_style)],
    ]
    t_sum = Table(summary_rows, colWidths=[140, 100, 264])
    t_sum.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_sum)
    story.append(Spacer(1, 10))

    # Detailed Flagged Issues Table
    story.append(Paragraph("2. Flagged Risk Items (Weighted Deductions)", h2_style))
    if flags:
        flag_rows = [
            [Paragraph("<b>ID / Ref</b>", body_style), Paragraph("<b>Category & Rule</b>", body_style), Paragraph("<b>Severity</b>", body_style), Paragraph("<b>Deduction</b>", body_style), Paragraph("<b>Explanation & Remedy</b>", body_style)]
        ]
        for f in flags:
            clause_ref = f"Clause {f.get('clause_id')}" if f.get('clause_id') else "Omission"
            severity_color = "#ef4444" if f.get("severity") == "HIGH" else ("#f59e0b" if f.get("severity") == "MEDIUM" else "#10b981")
            sev_p = Paragraph(f"<font color='{severity_color}'><b>{f.get('severity')}</b></font>", body_style)
            exp_p = Paragraph(f"<b>{f.get('explanation')}</b><br/><i>Remedy:</i> {f.get('recommendation')}", body_style)

            flag_rows.append([
                Paragraph(f"{f.get('flag_id')}<br/><font color='#64748b'>{clause_ref}</font>", body_style),
                Paragraph(f"<b>{f.get('category')}</b><br/>{f.get('rule_name')}", body_style),
                sev_p,
                Paragraph(f"-{f.get('deduction_points')} pts", body_style),
                exp_p,
            ])
        t_flags = Table(flag_rows, colWidths=[65, 115, 55, 55, 214])
        t_flags.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('BOX', (0,0), (-1,-1), 0.5, border_color),
            ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
            ('PADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(t_flags)
    else:
        story.append(Paragraph("No critical risk flags were identified for this contract.", body_style))

    story.append(Spacer(1, 10))

    # Clause Inventory Summary
    story.append(Paragraph("3. Classified Clauses Overview", h2_style))
    clauses = analysis_data.get("clauses", [])
    if clauses:
        clause_rows = [
            [Paragraph("<b>#</b>", body_style), Paragraph("<b>Heading / Title</b>", body_style), Paragraph("<b>Classified Category</b>", body_style), Paragraph("<b>Conf.</b>", body_style)]
        ]
        for c in clauses[:25]:  # Summarize up to 25 clauses
            cid = c.get("clause_id", 1)
            title = c.get("title") or c.get("clause_number") or f"Clause {cid}"
            cat = c.get("category", "General")
            conf = f"{int(c.get('confidence', 0.9) * 100)}%"
            clause_rows.append([
                Paragraph(str(cid), body_style),
                Paragraph(title[:45], body_style),
                Paragraph(cat.replace("_", " "), body_style),
                Paragraph(conf, body_style),
            ])
        t_clauses = Table(clause_rows, colWidths=[30, 240, 174, 60])
        t_clauses.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('BOX', (0,0), (-1,-1), 0.5, border_color),
            ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_clauses)

    doc.build(story, canvasmaker=ReportNumberedCanvas)
    return buffer.getvalue()
