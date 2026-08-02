"""
Results & Research Platform Screen Module
Executive single-view unified research platform combining:
- Session Summary Metadata
- Band Power Breakdown Matrix
- Cognitive Load & Stress Index Assessment
- One-Click PDF Report Exporter
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QGridLayout
from PySide6.QtCore import Qt, Signal
from src.app.config import COLOR_CARD_BG, COLOR_CYAN, COLOR_EMERALD, COLOR_PURPLE, COLOR_AMBER, COLOR_ROSE
from src.reporting.pdf_generator import PDFReportGenerator

class ResultsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf_generator = PDFReportGenerator()
        self.current_metrics = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header Title
        h_card = QFrame()
        h_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px;")
        h_layout = QHBoxLayout(h_card)

        t_box = QVBoxLayout()
        title = QLabel("UNIFIED RESULTS & RESEARCH ANALYTICS PLATFORM")
        title.setStyleSheet("font-size: 15px; font-weight: 900; color: #F8FAFC; letter-spacing: 1px;")
        sub = QLabel("Comprehensive Single-View Analytical Summary & Report Generator")
        sub.setStyleSheet("font-size: 11px; color: #94A3B8;")
        t_box.addWidget(title)
        t_box.addWidget(sub)

        btn_export = QPushButton("📄 EXPORT PDF REPORT")
        btn_export.setStyleSheet("background: linear-gradient(135deg, #06B6D4, #0284C7); color: white; font-weight: 800; font-size: 12px; padding: 12px 20px; border-radius: 8px; border: none;")
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.clicked.connect(self.export_pdf_report)

        h_layout.addLayout(t_box)
        h_layout.addStretch()
        h_layout.addWidget(btn_export)
        layout.addWidget(h_card)

        # Main Grid Layout
        grid_card = QFrame()
        grid_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 20px;")
        g_layout = QGridLayout(grid_card)
        g_layout.setSpacing(16)

        # Row 1: Key Performance Metrics
        self.val_load = self._create_result_box("CLASSIFIED COGNITIVE LOAD", "MODERATE", COLOR_CYAN, g_layout, 0, 0)
        self.val_stress = self._create_result_box("SPECTRAL STRESS INDEX", "0.48", COLOR_AMBER, g_layout, 0, 1)
        self.val_dom = self._create_result_box("DOMINANT RHYTHM", "ALPHA (10 Hz)", COLOR_PURPLE, g_layout, 0, 2)
        self.val_quality = self._create_result_box("SIGNAL QUALITY / SAMPLING", "EXCELLENT (250 Hz)", COLOR_EMERALD, g_layout, 0, 3)

        # Row 2: Band Breakdown Cards
        self.val_delta = self._create_result_box("DELTA POWER (0.5-4 Hz)", "25.0 %", COLOR_CYAN, g_layout, 1, 0)
        self.val_theta = self._create_result_box("THETA POWER (4-8 Hz)", "25.0 %", COLOR_EMERALD, g_layout, 1, 1)
        self.val_alpha = self._create_result_box("ALPHA POWER (8-13 Hz)", "25.0 %", COLOR_PURPLE, g_layout, 1, 2)
        self.val_beta  = self._create_result_box("BETA POWER (13-30 Hz)", "25.0 %", COLOR_AMBER, g_layout, 1, 3)

        layout.addWidget(grid_card)

    def _create_result_box(self, title, val, color, grid_layout, row, col):
        frame = QFrame()
        frame.setStyleSheet("background: rgba(15,23,42,0.8); border: 1px solid rgba(255,255,255,0.05); border-radius: 10px; padding: 14px;")
        l = QVBoxLayout(frame)
        
        t = QLabel(title)
        t.setStyleSheet("font-size: 10px; font-weight: 800; color: #94A3B8; letter-spacing: 1px;")
        
        v = QLabel(val)
        v.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {color}; margin-top: 4px;")

        l.addWidget(t)
        l.addWidget(v)

        grid_layout.addWidget(frame, row, col)
        return v

    def update_results(self, band_powers, metrics):
        self.current_metrics = metrics
        self.current_metrics.update(band_powers)

        self.val_delta.setText(f"{band_powers.get('delta_rel', 25.0):.1f} %")
        self.val_theta.setText(f"{band_powers.get('theta_rel', 25.0):.1f} %")
        self.val_alpha.setText(f"{band_powers.get('alpha_rel', 25.0):.1f} %")
        self.val_beta.setText(f"{band_powers.get('beta_rel', 25.0):.1f} %")

        self.val_stress.setText(f"{metrics.get('stress_index', 0.48):.2f}")
        self.val_dom.setText(metrics.get('dominant_band', 'ALPHA'))
        self.val_load.setText(metrics.get('load_class', 'MODERATE'))

    def export_pdf_report(self):
        filepath = self.pdf_generator.generate_report(self.current_metrics)
        alert_text = f"Report Generated Successfully!\nSaved to: {filepath}"
        print(alert_text)
