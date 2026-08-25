"""
Professional PDF Report Generator Module — NeuroSim 2.0
Creates research-grade clinical session reports using ReportLab.
Supports comprehensive session metadata, spectral analysis, signal quality metrics,
and AI interpretation narratives with research disclaimers.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
import os
import datetime
from typing import Dict, Any, List, Optional


class PDFReportGenerator:
    """
    Generates professional research session reports in PDF format.
    Supports comprehensive metadata, spectral breakdowns, signal quality assessment,
    and longitudinal comparisons.
    """

    def __init__(self, output_dir="reports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    @classmethod
    def generate_report(cls, session_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Generates comprehensive PDF report from session data dictionary.
        
        Args:
            session_data: Dictionary containing session metadata and metrics
            filename: Optional output filename (absolute or relative)
            
        Returns:
            Path to generated PDF file
        """
        if isinstance(cls, PDFReportGenerator):
            output_dir = cls.output_dir
        else:
            output_dir = "reports"
            os.makedirs(output_dir, exist_ok=True)

        if not isinstance(session_data, dict):
            session_data = {'id': str(session_data)}

        if filename is None:
            session_id = session_data.get('session_id', session_data.get('id', 'DEMO'))
            filename = f"NeuroSim_Session_{session_id}.pdf"
        
        if os.path.isabs(filename) or os.path.dirname(filename):
            filepath = filename
        else:
            filepath = os.path.join(output_dir, filename)

        doc = SimpleDocTemplate(
            filepath, 
            pagesize=A4, 
            leftMargin=50, 
            rightMargin=50, 
            topMargin=50, 
            bottomMargin=50
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'DocTitle', 
            parent=styles['Title'], 
            fontName='Helvetica-Bold', 
            fontSize=24, 
            textColor=colors.HexColor('#06B6D4'),
            alignment=1,  # Center
            spaceAfter=6
        )
        
        subtitle_style = ParagraphStyle(
            'DocSub', 
            parent=styles['Normal'], 
            fontName='Helvetica-Bold', 
            fontSize=10, 
            textColor=colors.HexColor('#64748B'),
            alignment=1,
            spaceAfter=12
        )
        
        h2_style = ParagraphStyle(
            'H2', 
            parent=styles['Heading2'], 
            fontName='Helvetica-Bold', 
            fontSize=13, 
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=14, 
            spaceAfter=8,
            borderWidth=0,
            borderPadding=0
        )
        
        body_style = ParagraphStyle(
            'Body', 
            parent=styles['BodyText'], 
            fontName='Helvetica', 
            fontSize=10, 
            leading=14, 
            textColor=colors.HexColor('#334155')
        )
        
        caption_style = ParagraphStyle(
            'Caption', 
            parent=styles['Normal'], 
            fontName='Helvetica-Oblique', 
            fontSize=9, 
            textColor=colors.HexColor('#64748B')
        )
        
        elements = []

        # Header
        elements.append(Paragraph("NeuroSim Analytics Report", title_style))
        elements.append(Paragraph("Intelligent EEG Cognitive Analytics Platform", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceBefore=0, spaceAfter=16))

        # Section 1: Session Metadata
        elements.append(Paragraph("SESSION METADATA", h2_style))
        
        metadata_table = cls._build_metadata_table(session_data, body_style)
        elements.append(metadata_table)
        elements.append(Spacer(1, 16))

        # Section 2: Spectral Band Analysis
        elements.append(Paragraph("SPECTRAL BAND POWER ANALYSIS", h2_style))
        
        band_table = cls._build_band_power_table(session_data, body_style)
        elements.append(band_table)
        elements.append(Spacer(1, 16))

        # Section 3: Signal Quality Metrics
        elements.append(Paragraph("SIGNAL QUALITY ASSESSMENT", h2_style))
        
        quality_table = cls._build_quality_table(session_data, body_style)
        elements.append(quality_table)
        elements.append(Spacer(1, 16))

        # Section 4: AI Narrative
        elements.append(Paragraph("AI NARRATIVE & INTERPRETATION", h2_style))
        ai_narrative = cls._generate_narrative(session_data)
        elements.append(Paragraph(ai_narrative, body_style))
        elements.append(Spacer(1, 20))
        
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceBefore=0, spaceAfter=12))
        
        # Disclaimer
        disclaimer_style = ParagraphStyle(
            'Foot', 
            parent=styles['Normal'], 
            fontSize=8, 
            textColor=colors.HexColor('#94A3B8'),
            alignment=1
        )
        elements.append(Paragraph(
            "<b>Disclaimer:</b> NeuroSim is an educational neural signal processing research simulation environment. "
            "Not intended for clinical diagnostic use. All analyses are for research and educational purposes only.",
            disclaimer_style
        ))

        doc.build(elements)
        return filepath

    @staticmethod
    def _build_metadata_table(session_data: Dict[str, Any], style: ParagraphStyle) -> Table:
        """Build session metadata table."""
        data = [
            [Paragraph("<b>Parameter</b>", style), Paragraph("<b>Value</b>", style)],
            ["Session ID", str(session_data.get('session_id', session_data.get('id', 'N/A')))],
            ["Timestamp", str(session_data.get('timestamp', 'N/A'))],
            ["Duration", f"{float(session_data.get('duration', 0.0)):.1f} seconds"],
            ["Sample Count", f"{int(session_data.get('sample_count', 0)):,} samples"],
            ["Sampling Rate", f"{int(session_data.get('sampling_rate', 250))} Hz"],
            ["Data Source", str(session_data.get('source', session_data.get('mode', 'SIMULATION')))],
            ["Channel Configuration", str(session_data.get('channel_info', '8-channel EEG'))],
            ["Dominant Frequency", f"{float(session_data.get('dominant_frequency', 10.0)):.2f} Hz"],
            ["Theta/Beta Ratio (TBR)", f"{float(session_data.get('tbr', 0.0)):.3f}"],
            ["Alpha/Beta Ratio (ABR)", f"{float(session_data.get('abr', 0.0)):.3f}"],
        ]

        t = Table(data, colWidths=[220, 280])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8FAFC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return t

    @staticmethod
    def _build_band_power_table(session_data: Dict[str, Any], style: ParagraphStyle) -> Table:
        """Build spectral band power breakdown table."""
        # Calculate total power
        delta = float(session_data.get('delta', session_data.get('rel_delta', 25.0)))
        theta = float(session_data.get('theta', session_data.get('rel_theta', 25.0)))
        alpha = float(session_data.get('alpha', session_data.get('rel_alpha', 25.0)))
        beta = float(session_data.get('beta', session_data.get('rel_beta', 25.0)))
        
        total_power = delta + theta + alpha + beta
        if total_power == 0:
            total_power = 100.0
        
        # Calculate relative percentages if not provided
        rel_delta = float(session_data.get('rel_delta', (delta / total_power) * 100))
        rel_theta = float(session_data.get('rel_theta', (theta / total_power) * 100))
        rel_alpha = float(session_data.get('rel_alpha', (alpha / total_power) * 100))
        rel_beta = float(session_data.get('rel_beta', (beta / total_power) * 100))
        
        data = [
            [Paragraph("<b>Band</b>", style), 
             Paragraph("<b>Frequency Range</b>", style), 
             Paragraph("<b>Absolute Power (μV²)</b>", style), 
             Paragraph("<b>Relative Power (%)</b>", style)],
            ["Delta (δ)", "0.5 - 4 Hz", f"{delta:.2f}", f"{rel_delta:.1f}%"],
            ["Theta (θ)", "4 - 8 Hz", f"{theta:.2f}", f"{rel_theta:.1f}%"],
            ["Alpha (α)", "8 - 13 Hz", f"{alpha:.2f}", f"{rel_alpha:.1f}%"],
            ["Beta (β)", "13 - 30 Hz", f"{beta:.2f}", f"{rel_beta:.1f}%"],
            [Paragraph("<b>Total Power</b>", style), "-", f"{total_power:.2f}", "100.0%"],
        ]

        t = Table(data, colWidths=[120, 120, 150, 110])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8FAFC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F1F5F9')),
        ]))
        return t

    @staticmethod
    def _build_quality_table(session_data: Dict[str, Any], style: ParagraphStyle) -> Table:
        """Build signal quality assessment table."""
        signal_quality = float(session_data.get('signal_quality', 85.0))
        noise_level = float(session_data.get('noise_level', 15.0))
        artifact_rate = float(session_data.get('artifact_rate', 5.0))
        snr = float(session_data.get('snr', 20.0))
        
        # Quality rating
        if signal_quality >= 90:
            rating = "EXCELLENT"
            rating_color = "#10B981"
        elif signal_quality >= 75:
            rating = "GOOD"
            rating_color = "#3B82F6"
        elif signal_quality >= 60:
            rating = "ACCEPTABLE"
            rating_color = "#F59E0B"
        else:
            rating = "POOR"
            rating_color = "#EF4444"
        
        data = [
            [Paragraph("<b>Metric</b>", style), Paragraph("<b>Value</b>", style), Paragraph("<b>Status</b>", style)],
            ["Overall Signal Quality", f"{signal_quality:.1f}%", rating],
            ["Noise Level", f"{noise_level:.1f}%", "LOW" if noise_level < 20 else "HIGH"],
            ["Artifact Rate", f"{artifact_rate:.1f}%", "LOW" if artifact_rate < 10 else "HIGH"],
            ["Signal-to-Noise Ratio (SNR)", f"{snr:.1f} dB", "GOOD" if snr > 15 else "LOW"],
            ["Cognitive Load Classification", str(session_data.get('cognitive_state', 'MODERATE')), "-"],
            ["Spectral Stress Index", f"{float(session_data.get('stress_index', 0.5)):.2f}", 
             "LOW" if float(session_data.get('stress_index', 0.5)) < 0.4 else "HIGH"],
            ["Classification Confidence", f"{float(session_data.get('confidence', 85.0)):.1f}%", 
             "HIGH" if float(session_data.get('confidence', 85.0)) > 80 else "MODERATE"],
        ]

        t = Table(data, colWidths=[200, 150, 150])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8FAFC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return t

    @staticmethod
    def _generate_narrative(session_data: Dict[str, Any]) -> str:
        """Generate AI interpretation narrative based on session data."""
        dominant_band = str(session_data.get('dominant_band', 'ALPHA'))
        stress_index = float(session_data.get('stress_index', 0.5))
        cognitive_state = str(session_data.get('cognitive_state', 'MODERATE'))
        signal_quality = float(session_data.get('signal_quality', 85.0))
        
        narrative_parts = []
        
        # Opening
        narrative_parts.append(
            f"The session exhibited {dominant_band.lower()} dominance in the spectral power distribution, "
            f"characteristic of a {cognitive_state.lower()} cognitive state."
        )
        
        # Stress analysis
        if stress_index < 0.3:
            narrative_parts.append(
                "Spectral stress indicators remained at minimal levels, suggesting relaxed mental engagement."
            )
        elif stress_index < 0.6:
            narrative_parts.append(
                "Moderate stress indices were observed, consistent with focused attentional demands."
            )
        else:
            narrative_parts.append(
                "Elevated stress markers were detected, potentially indicating high cognitive load or mental fatigue."
            )
        
        # Signal quality note
        if signal_quality >= 85:
            narrative_parts.append(
                "Signal quality was excellent throughout the recording session with minimal artifacts."
            )
        elif signal_quality >= 60:
            narrative_parts.append(
                "Acceptable signal quality was maintained with occasional artifact contamination."
            )
        else:
            narrative_parts.append(
                "Signal quality was compromised by artifacts; interpretation should be made with caution."
            )
        
        return " ".join(narrative_parts)
