"""
Biomedical PDF Report Generator Module
Creates medical-grade clinical & cognitive load session reports using ReportLab.
Features header branding, patient demographics, cognitive workload evaluation,
spectral band decomposition, patient condition diagnosis, prescriptive guidance,
and research disclaimers.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class PDFReportGenerator:
    """
    Generates research & clinical session diagnostic reports in PDF format.
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
            filename = f"NeuroSim_Cognitive_Report_{session_data.get('session_id', session_data.get('id', 'LIVE'))}.pdf"

        if os.path.isabs(filename) or os.path.dirname(filename):
            filepath = filename
        else:
            filepath = os.path.join(output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom Typography
        title_style = ParagraphStyle('DocTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=colors.HexColor('#0284C7'), alignment=0)
        subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=colors.HexColor('#475569'))
        h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=colors.HexColor('#0F172A'), spaceBefore=10, spaceAfter=4)
        body_style = ParagraphStyle('Body', parent=styles['BodyText'], fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor('#334155'))
        body_bold = ParagraphStyle('BodyBold', parent=styles['BodyText'], fontName='Helvetica-Bold', fontSize=9, leading=13, textColor=colors.HexColor('#0F172A'))
        callout_style = ParagraphStyle('Callout', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor('#1E293B'))

        elements = []

        # 1. Header Banner
        elements.append(Paragraph("NEUROSIM &bull; CLINICAL COGNITIVE LOAD REPORT", title_style))
        elements.append(Paragraph("Electrophysiological Brainwave Diagnostics &bull; 3-Electrode Bio-Potential Acquisition", subtitle_style))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0284C7'), spaceBefore=0, spaceAfter=8))

        # 2. Patient & Session Metadata Table
        pat_id = str(session_data.get('patient_id', 'PAT-001'))
        sess_id = str(session_data.get('session_id', session_data.get('id', 'SESS-LIVE')))
        clinician = str(session_data.get('clinician', 'Dr. Barathwaj V (Lead Neuroengineer)'))
        date_str = str(session_data.get('timestamp', session_data.get('date', 'Live Telemetry Session')))
        src_str = str(session_data.get('source', '3-Electrode Hardware (E1 Active, E2 Ref, E3 GND) + Aux Sensor'))

        meta_data = [
            [
                Paragraph(f"<b>Patient / Subject ID:</b> {pat_id}", body_style),
                Paragraph(f"<b>Session Reference:</b> {sess_id}", body_style)
            ],
            [
                Paragraph(f"<b>Attending Clinician:</b> {clinician}", body_style),
                Paragraph(f"<b>Acquisition Timestamp:</b> {date_str}", body_style)
            ],
            [
                Paragraph(f"<b>Signal Pipeline:</b> {src_str}", body_style),
                Paragraph(f"<b>Sampling Frequency:</b> 250 Hz Clinical Standard", body_style)
            ]
        ]
        t_meta = Table(meta_data, colWidths=[270, 270])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t_meta)
        elements.append(Spacer(1, 8))

        # 3. Cognitive Workload Classification & Status Box
        cog_state = str(session_data.get('cognitive_state', session_data.get('load_class', 'MODERATE'))).upper()
        conf = float(session_data.get('confidence', session_data.get('ml_conf', 85.0)))
        stress = float(session_data.get('stress_index', 0.45))
        dom_band = str(session_data.get('dominant_band', 'ALPHA (10.0 Hz)'))

        state_color = colors.HexColor('#EF4444') if cog_state == 'HIGH' else (colors.HexColor('#0284C7') if cog_state == 'MODERATE' else colors.HexColor('#10B981'))

        elements.append(Paragraph("1. COGNITIVE WORKLOAD & ATTENTIONAL DIAGNOSIS", h2_style))
        summary_cards = [
            [
                Paragraph("<b>CLASSIFIED COGNITIVE STATE</b>", subtitle_style),
                Paragraph("<b>AI MODEL CONFIDENCE</b>", subtitle_style),
                Paragraph("<b>SPECTRAL STRESS INDEX</b>", subtitle_style),
                Paragraph("<b>DOMINANT RHYTHM</b>", subtitle_style)
            ],
            [
                Paragraph(f"<b><font size='13' color='{state_color.hexval()}'>{cog_state} WORKLOAD</font></b>", body_style),
                Paragraph(f"<b><font size='12' color='#0284C7'>{conf:.1f}%</font></b>", body_style),
                Paragraph(f"<b><font size='12' color='#D97706'>{stress:.2f}</font></b>", body_style),
                Paragraph(f"<b><font size='11' color='#0284C7'>{dom_band}</font></b>", body_style)
            ]
        ]
        t_cards = Table(summary_cards, colWidths=[135, 135, 135, 135])
        t_cards.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(t_cards)
        elements.append(Spacer(1, 8))

        # 4. Extracted Electrophysiological Band Decomposition Table
        elements.append(Paragraph("2. EXTRACTED BRAINWAVE SPECTRAL DECOMPOSITION", h2_style))

        d_p = float(session_data.get('rel_delta', session_data.get('delta', 25.0)))
        t_p = float(session_data.get('rel_theta', session_data.get('theta', 25.0)))
        a_p = float(session_data.get('rel_alpha', session_data.get('alpha', 25.0)))
        b_p = float(session_data.get('rel_beta', session_data.get('beta', 25.0)))
        tbr = float(session_data.get('tbr', (t_p / max(0.1, b_p))))
        abr = float(session_data.get('abr', (a_p / max(0.1, b_p))))

        band_table_data = [
            [Paragraph("<b>Frequency Band</b>", body_bold), Paragraph("<b>Spectral Range</b>", body_bold), Paragraph("<b>Relative Power</b>", body_bold), Paragraph("<b>Clinical Neurological Interpretation</b>", body_bold)],
            ["Delta (\u03b4)", "0.5 - 4.0 Hz", f"{d_p:.1f} %", "Subcortical restorative slow waves; baseline somnolence / restorative depth."],
            ["Theta (\u03b8)", "4.0 - 8.0 Hz", f"{t_p:.1f} %", "Hippocampal-prefrontal working memory consolidation & navigational load."],
            ["Alpha (\u03b1)", "8.0 - 13.0 Hz", f"{a_p:.1f} %", "Cortical sensory gating; calm relaxed alertness; optimal task readiness."],
            ["Beta (\u03b2)", "13.0 - 30.0 Hz", f"{b_p:.1f} %", "Active executive cognitive processing; problem solving & mental strain."],
            ["Theta/Beta Ratio", "TBR Metric", f"{tbr:.2f}", "Executive attentional control index (clinical reference: < 2.0)."],
            ["Alpha/Beta Ratio", "ABR Metric", f"{abr:.2f}", "Arousal vs relaxation equilibrium index (clinical reference: 0.8 - 1.5)."]
        ]
        t_bands = Table(band_table_data, colWidths=[100, 75, 75, 290])
        t_bands.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
            ('ALIGN', (0,0), (2,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(t_bands)
        elements.append(Spacer(1, 8))

        # 5. Patient Condition Assessment Narrative
        elements.append(Paragraph("3. PATIENT NEUROLOGICAL CONDITION ASSESSMENT", h2_style))

        if cog_state == 'HIGH':
            cond_narrative = (
                f"<b>Acute Cognitive Overload & Elevated Cortical Arousal:</b> The patient demonstrates pronounced "
                f"high-frequency beta band synchrony ({b_p:.1f}%) paired with an elevated Spectral Stress Index of {stress:.2f}. "
                f"This electrophysiological signature reflects acute executive task strain, heightened attentional demands, "
                f"and potential mental exhaustion. Alpha power ({a_p:.1f}%) is suppressed, indicating active sensory engagement "
                f"without adequate restorative neurological pausing."
            )
        elif cog_state == 'LOW':
            cond_narrative = (
                f"<b>Attentional Deceleration & Potential Cognitive Fatigue:</b> The patient exhibits prominent low-frequency "
                f"power across delta ({d_p:.1f}%) and theta ({t_p:.1f}%) bands, with a subdued Beta processing index ({b_p:.1f}%). "
                f"This pattern corresponds with low task engagement, mental fatigue, or transitioning into somnolence. "
                f"Working memory consolidation is dominant over active problem-solving execution."
            )
        else:
            cond_narrative = (
                f"<b>Nominal Balanced Cognitive Flow State:</b> The electrophysiological telemetry exhibits an optimal, "
                f"synchronized alpha rhythm ({a_p:.1f}%) with a dominant frequency of {dom_band}. "
                f"The Spectral Stress Index ({stress:.2f}) and Theta/Beta ratio ({tbr:.2f}) reside comfortably within standard "
                f"normative research baselines. The patient maintains sustained attentional readiness without evidence of acute mental fatigue."
            )

        elements.append(Paragraph(cond_narrative, body_style))
        elements.append(Spacer(1, 8))

        # 6. Prescriptive Patient Action Plan ("What Should the Patient Do")
        elements.append(Paragraph("4. CLINICAL PATIENT ACTION PLAN (PRESCRIPTIVE GUIDANCE)", h2_style))

        if cog_state == 'HIGH':
            actions = [
                "<b>1. Immediate Cognitive Pacing:</b> Institute a structured 10 to 15-minute sensory rest period. Disengage from high-density computer tasks or complex problem-solving.",
                "<b>2. Sensory De-Escalation:</b> Dim ambient screen brightness and minimize dual-task acoustic distractions to permit fronto-cortical alpha rhythm recovery.",
                "<b>3. Paced Breathing Biofeedback:</b> Perform 5 minutes of 0.1 Hz diaphragmatic breathing (6 breaths per minute) to stimulate parasympathetic tone and reduce cortical beta over-activation.",
                "<b>4. Re-Assessment Protocol:</b> Repeat the 3-lead electrophysiological assessment after a 30-minute rest interval to verify normalization of the Spectral Stress Index (<0.60)."
            ]
        elif cog_state == 'LOW':
            actions = [
                "<b>1. Task Re-Activation:</b> Introduce brief physical posture adjustment, dynamic stretching, or active task segmenting to counter attentional drowsiness.",
                "<b>2. Environmental Alertness Calibration:</b> Increase environmental ambient lighting and introduce structured 15-minute focused work intervals.",
                "<b>3. Hydration & Metabolic Check:</b> Ensure adequate hydration and verify sleep-wake circadian alignment.",
                "<b>4. Follow-Up Assessment:</b> Repeat baseline acquisition during mid-morning peak arousal hours."
            ]
        else:
            actions = [
                "<b>1. Maintain Current Task Parameters:</b> Patient is operating at optimal cognitive flow; safe to continue high-precision analytical tasks.",
                "<b>2. Preventative Break Scheduling:</b> Enforce 5-minute restorative micro-breaks every 50 minutes to preserve attentional stamina.",
                "<b>3. Routine Monitoring:</b> Schedule periodic follow-up checks during extended high-demand experimental sessions."
            ]

        for act in actions:
            elements.append(Paragraph(f"&bull; {act}", callout_style))
            elements.append(Spacer(1, 3))

        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceBefore=0, spaceAfter=6))

        # 7. Sign-off and Medical Disclaimer
        disclaimer = (
            "<b>Clinical & Research Disclaimer:</b> NeuroSim is an advanced neural signal analytics and cognitive load research workstation. "
            "Report output is calibrated using 3-electrode differential biopotential telemetry and deep neural network classification. "
            "Final diagnosis and therapeutic decisions must be corroborated by a qualified medical professional."
        )
        elements.append(Paragraph(disclaimer, ParagraphStyle('Foot', parent=styles['Normal'], fontSize=7.5, leading=10, textColor=colors.HexColor('#94A3B8'))))

        doc.build(elements)
        return filepath
