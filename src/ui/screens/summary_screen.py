"""
Screen 6 — Post-Session Analysis Result Screen
Comprehensive post-recording summary, average band percentages, state distribution, and report action.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout
from PySide6.QtCore import Qt, Signal
from src.app.config import COLORS
from src.visualization.custom_widgets import GlassCard, MetricCard, BandPowerBar

class SummaryScreen(QWidget):
    generate_report_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("POST-SESSION ANALYSIS SUMMARY")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(14)

        self.m_dur = MetricCard("Total Recording Duration", "04:32", "", "Session Elapsed Time", COLORS['accent_cyan'])
        self.m_dom = MetricCard("Dominant Band", "ALPHA", "", "10.0 Hz Mean Peak", COLORS['accent_purple'])
        self.m_load = MetricCard("Avg Cognitive Workload", "MODERATE", "", "Primary Predicted State", COLORS['accent_emerald'])
        self.m_stress = MetricCard("Avg Stress Index", "0.48", "", "Balanced Arousal", COLORS['accent_amber'])

        grid.addWidget(self.m_dur, 0, 0)
        grid.addWidget(self.m_dom, 0, 1)
        grid.addWidget(self.m_load, 0, 2)
        grid.addWidget(self.m_stress, 0, 3)

        layout.addLayout(grid)

        # Average Band Activity Card
        bands_card = GlassCard()
        b_layout = QVBoxLayout(bands_card)
        b_layout.setContentsMargins(20, 16, 20, 16)

        b_title = QLabel("AVERAGE BAND ACTIVITY OVER SESSION")
        b_title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {COLORS['text_muted']}; letter-spacing: 1px;")
        b_layout.addWidget(b_title)

        self.bar_d = BandPowerBar("Delta (δ)", "0.5-4 Hz", COLORS['accent_cyan'])
        self.bar_t = BandPowerBar("Theta (θ)", "4-8 Hz", COLORS['accent_emerald'])
        self.bar_a = BandPowerBar("Alpha (α)", "8-13 Hz", COLORS['accent_purple'])
        self.bar_b = BandPowerBar("Beta (β)", "13-30 Hz", COLORS['accent_amber'])

        b_layout.addWidget(self.bar_d)
        b_layout.addWidget(self.bar_t)
        b_layout.addWidget(self.bar_a)
        b_layout.addWidget(self.bar_b)

        layout.addWidget(bands_card)

        # Action bar to generate PDF report
        act_row = QHBoxLayout()
        act_row.addStretch()

        self.gen_btn = QPushButton("📄 GENERATE PDF ANALYSIS REPORT →")
        self.gen_btn.setProperty("class", "PrimaryBtn")
        self.gen_btn.setStyleSheet(f"background: {COLORS['accent_cyan']}; font-size: 14px; padding: 12px 24px;")
        self.gen_btn.clicked.connect(self.generate_report_requested.emit)

        act_row.addWidget(self.gen_btn)
        layout.addLayout(act_row)
        layout.addStretch()

    def set_summary_data(self, session_data: dict):
        dur = float(session_data.get('duration', 0.0))
        mins = int(dur) // 60
        secs = int(dur) % 60
        self.m_dur.update_value(f"{mins:02d}:{secs:02d}")

        self.m_dom.update_value(session_data.get('dominant_band', 'ALPHA'))
        self.m_load.update_value(session_data.get('cognitive_state', 'MODERATE'))
        self.m_stress.update_value(f"{session_data.get('stress_index', 0.48):.2f}")

        self.bar_d.set_percentage(session_data.get('rel_delta', 25.0))
        self.bar_t.set_percentage(session_data.get('rel_theta', 25.0))
        self.bar_a.set_percentage(session_data.get('rel_alpha', 25.0))
        self.bar_b.set_percentage(session_data.get('rel_beta', 25.0))
