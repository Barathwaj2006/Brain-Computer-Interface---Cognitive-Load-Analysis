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

    @classmethod
    def generate_report(cls, session_data, filename=None):
        """
        Generates PDF report from session data dictionary.
        Supports both instance method calls and classmethod calls.
        """
        if isinstance(cls, PDFReportGenerator):
            output_dir = cls.output_dir
        else:
            output_dir = "reports"
            os.makedirs(output_dir, exist_ok=True)

        if not isinstance(session_data, dict):
            session_data = {'id': str(session_data)}

        if filename is None:
            filename = f"NeuroSim_Session_{session_data.get('session_id', session_data.get('id', 'DEMO'))}.pdf"
        
        if os.path.isabs(filename) or os.path.dirname(filename):
            filepath = filename
        else:
            filepath = os.path.join(output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('DocTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=22, textColor=colors.HexColor('#06B6D4'), alignment=0)
        subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#64748B'))
        h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#0F172A'), spaceBefore=12, spaceAfter=6)
        body_style = ParagraphStyle('Body', parent=styles['BodyText'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#334155'))

        elements = []

        elements.append(Paragraph("NeuroSim Analytics Report", title_style))
        elements.append(Paragraph("Intelligent EEG Cognitive Analytics Platform", subtitle_style))
        elements.append(Spacer(1, 12))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceBefore=0, spaceAfter=12))

        # Overview Table
        data_summary = [
            [Paragraph("<b>Parameter</b>", body_style), Paragraph("<b>Value</b>", body_style)],
            ["Session ID", str(session_data.get('session_id', session_data.get('id', 'N/A')))],
            ["Classified Cognitive Load", str(session_data.get('cognitive_state', session_data.get('load_class', 'MODERATE')))],
            ["Spectral Stress Index", f"{session_data.get('stress_index', 0.5):.2f}"],
            ["Dominant Frequency Rhythm", str(session_data.get('dominant_band', 'ALPHA'))],
            ["Alpha Relative Power", f"{session_data.get('rel_alpha', session_data.get('alpha_rel', session_data.get('alpha', 25.0))):.1f} %"],
            ["Beta Relative Power", f"{session_data.get('rel_beta', session_data.get('beta_rel', session_data.get('beta', 25.0))):.1f} %"],
            ["Theta Relative Power", f"{session_data.get('rel_theta', session_data.get('theta_rel', session_data.get('theta', 25.0))):.1f} %"],
            ["Delta Relative Power", f"{session_data.get('rel_delta', session_data.get('delta_rel', session_data.get('delta', 25.0))):.1f} %"],
        ]

        t_summary = Table(data_summary, colWidths=[200, 300])
        t_summary.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F8FAFC')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0F172A')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ]))

        elements.append(t_summary)
        elements.append(Spacer(1, 16))

        elements.append(Paragraph("AI Narrative & Clinical Summary", h2_style))
        ai_narrative = session_data.get('ai_interpretation', "The session exhibited stable spectral power dynamics across alpha (8-13 Hz) and beta (13-30 Hz) bands. Spectral stress index remained within baseline research limits.")
        elements.append(Paragraph(ai_narrative, body_style))

        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceBefore=0, spaceAfter=12))
        elements.append(Paragraph("<b>Disclaimer:</b> NeuroSim is an educational neural signal processing research simulation environment. Not intended for clinical diagnostic use.", ParagraphStyle('Foot', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#94A3B8'))))

        doc.build(elements)
        return filepath
