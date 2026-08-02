"""
PDF Report Generator Module
Creates research-grade clinical session reports using ReportLab.
Features header branding, band breakdown table, AI interpretation narrative,
and research disclaimers.
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os

class PDFReportGenerator:
    """
    Generates research session reports in PDF format.
    """

    def __init__(self, output_dir="reports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_report(self, session_data, filename=None):
        """
        Generates PDF report from session data dictionary.
        """
        if filename is None:
            filename = f"NeuroSim_Session_{session_data.get('id', 'DEMO')}.pdf"
        
        filepath = os.path.join(self.output_dir, filename)
        doc = SimpleDocTemplate(filepath, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('DocTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=22, textColor=colors.HexColor('#06B6D4'), alignment=0)
        subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#64748B'))
        h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#0F172A'), spaceBefore=12, spaceAfter=6)
        body_style = ParagraphStyle('Body', parent=styles['BodyText'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#334155'))

        elements = []

        # Header Branding
        elements.append(Paragraph("NEUROSIM RESEARCH REPORT", title_style))
        elements.append(Paragraph("INTELLIGENT EEG COGNITIVE ANALYTICS PLATFORM", subtitle_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#06B6D4'), spaceAfter=15))

        # Session Metadata Table
        meta_data = [
            [Paragraph("<b>Session ID:</b>", body_style), Paragraph(str(session_data.get('id', 'SESS-001')), body_style),
             Paragraph("<b>Date:</b>", body_style), Paragraph(str(session_data.get('date', '2026-08-02')), body_style)],
            [Paragraph("<b>Duration:</b>", body_style), Paragraph(str(session_data.get('duration', '05:00')), body_style),
             Paragraph("<b>Sampling Freq:</b>", body_style), Paragraph("250 Hz", body_style)],
            [Paragraph("<b>Signal Source:</b>", body_style), Paragraph("Signal Simulator", body_style),
             Paragraph("<b>Classification:</b>", body_style), Paragraph(str(session_data.get('load_class', 'MODERATE')), body_style)]
        ]

        t_meta = Table(meta_data, colWidths=[100, 160, 100, 160])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t_meta)
        elements.append(Spacer(1, 15))

        # Band Breakdown Table
        elements.append(Paragraph("SPECTRAL BAND POWER BREAKDOWN", h2_style))
        band_table_data = [
            ["Band", "Frequency Range", "Relative Power (%)", "Clinical Context"],
            ["Delta (δ)", "0.5 – 4.0 Hz", f"{session_data.get('delta', 25.0):.1f}%", "Deep sleep, slow-wave activity"],
            ["Theta (θ)", "4.0 – 8.0 Hz", f"{session_data.get('theta', 25.0):.1f}%", "Drowsiness, meditation, memory"],
            ["Alpha (α)", "8.0 – 13.0 Hz", f"{session_data.get('alpha', 25.0):.1f}%", "Relaxed alertness, calm focus"],
            ["Beta (β)", "13.0 – 30.0 Hz", f"{session_data.get('beta', 25.0):.1f}%", "Active concentration, stress"]
        ]
        
        t_bands = Table(band_table_data, colWidths=[90, 110, 120, 200])
        t_bands.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#06B6D4')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t_bands)
        elements.append(Spacer(1, 15))

        # AI Session Narrative Interpretation
        elements.append(Paragraph("AI NARRATIVE INTERPRETATION", h2_style))
        ai_narrative = session_data.get('ai_interpretation', (
            "The recorded synthetic signal showed predominantly alpha-band activity throughout the session, "
            "with moderate beta activity. The calculated feature profile remained stable, while the cognitive-load "
            "classifier remained within the moderate category."
        ))
        elements.append(Paragraph(ai_narrative, body_style))
        elements.append(Spacer(1, 20))

        # Research Disclaimer
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#EF4444'), spaceAfter=10))
        disclaimer_text = (
            "<b>RESEARCH SYSTEM DISCLAIMER:</b> NeuroSim processes synthetic EEG-like signals for research, "
            "simulation, and analytical modeling. Analytical metrics do not constitute a medical diagnosis."
        )
        elements.append(Paragraph(disclaimer_text, body_style))

        doc.build(elements)
        return filepath
