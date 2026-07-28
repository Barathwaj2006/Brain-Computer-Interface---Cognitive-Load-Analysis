"""
Biomedical PDF Report Generator Module
Creates styled PDF reports using ReportLab with clinical session metadata, EEG spectral breakdown,
stress metrics, visual charts, and biomedical disclaimers.
"""

import os
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart

class PDFReportGenerator:
    @staticmethod
    def generate_report(session_data: Dict[str, Any], output_path: str) -> str:
        """
        Generate a professional biomedical PDF report.
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom Palette
        c_dark = colors.HexColor("#0B0F19")
        c_primary = colors.HexColor("#06B6D4")
        c_secondary = colors.HexColor("#8B5CF6")
        c_text = colors.HexColor("#1E293B")
        c_card_bg = colors.HexColor("#F8FAFC")

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=c_primary,
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=15
        )

        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=c_text,
            spaceBefore=12,
            spaceAfter=8
        )

        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=c_text
        )

        disclaimer_style = ParagraphStyle(
            'DisclaimerText',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#DC2626")
        )

        elements = []

        # Title Header
        elements.append(Paragraph("NEUROSIM", title_style))
        elements.append(Paragraph("Synthetic EEG Cognitive Analysis & Clinical Stress Report", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=2, color=c_primary, spaceAfter=15))

        # Session Metadata Table
        meta_data = [
            [
                Paragraph(f"<b>Session ID:</b> {session_data.get('session_id', 'N/A')}", body_style),
                Paragraph(f"<b>Date & Time:</b> {session_data.get('timestamp', 'N/A')}", body_style)
            ],
            [
                Paragraph(f"<b>Duration:</b> {session_data.get('duration', 0.0):.1f} sec", body_style),
                Paragraph(f"<b>Sampling Rate:</b> {session_data.get('sampling_rate', 250)} Hz", body_style)
            ],
            [
                Paragraph(f"<b>Signal Mode:</b> {session_data.get('mode', 'SIMULATION')}", body_style),
                Paragraph(f"<b>Dominant Band:</b> {session_data.get('dominant_band', 'ALPHA')}", body_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[270, 270])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), c_card_bg),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 15))

        # EEG Spectral Band Power Breakdown Table
        elements.append(Paragraph("1. Spectral Band Power Breakdown", heading_style))

        d_p = session_data.get('rel_delta', 25.0)
        t_p = session_data.get('rel_theta', 25.0)
        a_p = session_data.get('rel_alpha', 25.0)
        b_p = session_data.get('rel_beta', 25.0)

        band_table_data = [
            ['Frequency Band', 'Frequency Range', 'Relative Power (%)', 'Clinical Interpretation'],
            ['Delta (δ)', '0.5 – 4.0 Hz', f'{d_p:.1f} %', 'Deep rest, slow-wave sleep, low arousal'],
            ['Theta (θ)', '4.0 – 8.0 Hz', f'{t_p:.1f} %', 'Drowsiness, deep relaxation, meditation'],
            ['Alpha (α)', '8.0 – 13.0 Hz', f'{a_p:.1f} %', 'Relaxed alertness, calm mental focus'],
            ['Beta (β)', '13.0 – 30.0 Hz', f'{b_p:.1f} %', 'Active concentration, high workload, stress']
        ]

        band_table = Table(band_table_data, colWidths=[110, 110, 110, 210])
        band_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), c_primary),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), c_card_bg),
        ]))
        elements.append(band_table)
        elements.append(Spacer(1, 15))

        # Visual Chart (ReportLab VerticalBarChart)
        elements.append(Paragraph("2. Relative Band Distribution Chart", heading_style))
        chart_drawing = Drawing(540, 140)
        bc = VerticalBarChart()
        bc.x = 40
        bc.y = 20
        bc.height = 100
        bc.width = 460
        bc.data = [[d_p, t_p, a_p, b_p]]
        bc.categoryAxis.categoryNames = ['Delta', 'Theta', 'Alpha', 'Beta']
        bc.bars[0].fillColor = colors.HexColor("#06B6D4")
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = 100
        bc.valueAxis.valueStep = 25
        chart_drawing.add(bc)
        elements.append(chart_drawing)
        elements.append(Spacer(1, 15))

        # Cognitive State & Stress Diagnostics Card
        elements.append(Paragraph("3. Synthetic Cognitive Load & Stress Diagnostics", heading_style))

        cog_state = session_data.get('cognitive_state', 'MODERATE')
        stress_idx = session_data.get('stress_index', 0.5)
        conf = session_data.get('confidence', 85.0)

        diag_text = f"""
        <b>Cognitive Workload Level:</b> {cog_state}<br/>
        <b>Spectral Stress Index:</b> {stress_idx:.2f}<br/>
        <b>Classifier Confidence:</b> {conf:.1f}%<br/>
        <b>Clinical Assessment Note:</b> Synthetic pattern demonstrates {cog_state.lower()} cognitive arousal with primary dominance in the <b>{session_data.get('dominant_band', 'ALPHA')}</b> band.
        """
        diag_table = Table([[Paragraph(diag_text, body_style)]], colWidths=[540])
        diag_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#93C5FD")),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(diag_table)
        elements.append(Spacer(1, 20))

        # Mandatory Biomedical Disclaimer Notice Box
        disclaimer_box_data = [[
            Paragraph(
                "<b>MANDATORY BIOMEDICAL DISCLAIMER:</b><br/>"
                "This prototype analyses synthetic EEG-like signals for demonstration and development purposes. "
                "The results are not a medical diagnosis or validated assessment of a person's neurological or psychological condition.",
                disclaimer_style
            )
        ]]
        disclaimer_table = Table(disclaimer_box_data, colWidths=[540])
        disclaimer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#FCA5A5")),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(disclaimer_table)

        doc.build(elements)
        return output_path
