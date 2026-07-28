"""
Screen 4 — Band Analysis Screen
Detailed spectral power analysis, clinical ratios (TBR, ABR, Stress Index), and biofeedback assistant.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QPushButton
from PySide6.QtCore import Qt
from src.app.config import COLORS
from src.visualization.custom_widgets import GlassCard, MetricCard
from src.visualization.biofeedback_widget import BiofeedbackBreathingWidget

class BandAnalysisScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("CLINICAL SPECTRAL BAND ANALYSIS & RATIOS")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(14)

        self.m_delta = MetricCard("Delta Power (0.5-4 Hz)", "25.0 %", "", "Slow-Wave Activity", COLORS['accent_cyan'])
        self.m_theta = MetricCard("Theta Power (4-8 Hz)", "25.0 %", "", "Drowsiness & Memory", COLORS['accent_emerald'])
        self.m_alpha = MetricCard("Alpha Power (8-13 Hz)", "25.0 %", "", "Relaxed Alertness", COLORS['accent_purple'])
        self.m_beta  = MetricCard("Beta Power (13-30 Hz)", "25.0 %", "", "Active Concentration", COLORS['accent_amber'])

        self.m_tbr = MetricCard("Theta/Beta Ratio (TBR)", "1.00", "", "Cognitive Fatigue Metric", COLORS['accent_cyan'])
        self.m_abr = MetricCard("Alpha/Beta Ratio (ABR)", "1.00", "", "Relaxation vs Focus", COLORS['accent_purple'])
        self.m_stress = MetricCard("Spectral Stress Index", "0.50", "", "Beta / (Alpha + Theta)", COLORS['accent_rose'])
        self.m_engage = MetricCard("Engagement Index", "0.50", "", "Attentional Focus Score", COLORS['accent_emerald'])

        grid.addWidget(self.m_delta, 0, 0)
        grid.addWidget(self.m_theta, 0, 1)
        grid.addWidget(self.m_alpha, 0, 2)
        grid.addWidget(self.m_beta, 0, 3)

        grid.addWidget(self.m_tbr, 1, 0)
        grid.addWidget(self.m_abr, 1, 1)
        grid.addWidget(self.m_stress, 1, 2)
        grid.addWidget(self.m_engage, 1, 3)

        layout.addLayout(grid)

        # Biofeedback Guided Assistant Card
        bio_card = GlassCard()
        bio_layout = QHBoxLayout(bio_card)
        bio_layout.setContentsMargins(20, 16, 20, 16)

        info_box = QVBoxLayout()
        bio_title = QLabel("CLINICAL BIOFEEDBACK BREATHING ASSISTANT")
        bio_title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLORS['text_muted']}; letter-spacing: 1px;")
        bio_desc = QLabel("Guided 4-7-8 breathing protocol to reduce sympathetic stress arousal and elevate Alpha/Theta power.")
        bio_desc.setStyleSheet(f"font-size: 11px; color: {COLORS['text_secondary']};")

        btn_box = QHBoxLayout()
        self.btn_start_bio = QPushButton("START GUIDED SESSION")
        self.btn_start_bio.setProperty("class", "PrimaryBtn")
        self.btn_start_bio.clicked.connect(self._toggle_bio)

        btn_box.addWidget(self.btn_start_bio)
        btn_box.addStretch()

        info_box.addWidget(bio_title)
        info_box.addWidget(bio_desc)
        info_box.addLayout(btn_box)

        self.bio_widget = BiofeedbackBreathingWidget(self)

        bio_layout.addLayout(info_box, stretch=2)
        bio_layout.addWidget(self.bio_widget, stretch=1)

        layout.addWidget(bio_card)
        layout.addStretch()

    def _toggle_bio(self):
        if self.bio_widget.is_active:
            self.bio_widget.stop_guide()
            self.btn_start_bio.setText("START GUIDED SESSION")
        else:
            self.bio_widget.start_guide()
            self.btn_start_bio.setText("STOP GUIDED SESSION")

    def update_metrics(self, psd_metrics: dict):
        rel = psd_metrics.get('rel_powers', {})
        self.m_delta.update_value(f"{rel.get('delta', 25.0):.1f}", "%")
        self.m_theta.update_value(f"{rel.get('theta', 25.0):.1f}", "%")
        self.m_alpha.update_value(f"{rel.get('alpha', 25.0):.1f}", "%")
        self.m_beta.update_value(f"{rel.get('beta', 25.0):.1f}", "%")

        self.m_tbr.update_value(f"{psd_metrics.get('theta_beta_ratio', 1.0):.2f}")
        self.m_abr.update_value(f"{psd_metrics.get('alpha_beta_ratio', 1.0):.2f}")
        self.m_stress.update_value(f"{psd_metrics.get('stress_index', 0.5):.2f}")
        self.m_engage.update_value(f"{psd_metrics.get('engagement_index', 0.5):.2f}")
