"""
Screen 7 — PDF Report Generator Screen
Generate, view, and export professional biomedical PDF analysis reports.
"""

import os
import subprocess
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox
from PySide6.QtCore import Qt
from src.app.config import COLORS
from src.visualization.custom_widgets import GlassCard
from src.reporting.pdf_generator import PDFReportGenerator

class ReportScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_pdf_path = ""
        self.current_session_data = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("BIOMEDICAL PDF REPORT GENERATOR")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        layout.addWidget(title)

        card = GlassCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        sub = QLabel("Export a clinical PDF report containing session metadata, EEG band breakdown tables, charts, and disclaimers.")
        sub.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        card_layout.addWidget(sub)

        self.status_lbl = QLabel("Report Status: Ready to Generate")
        self.status_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLORS['accent_cyan']};")
        card_layout.addWidget(self.status_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        self.btn_gen = QPushButton("⚡ GENERATE PDF REPORT")
        self.btn_gen.setProperty("class", "PrimaryBtn")
        self.btn_gen.setStyleSheet(f"background: {COLORS['accent_cyan']}; font-size: 14px; padding: 12px 24px;")
        self.btn_gen.clicked.connect(self._do_generate)

        self.btn_open = QPushButton("👁 OPEN PDF REPORT")
        self.btn_open.setProperty("class", "SecondaryBtn")
        self.btn_open.setEnabled(False)
        self.btn_open.clicked.connect(self._open_pdf)

        self.btn_save = QPushButton("💾 SAVE REPORT AS...")
        self.btn_save.setProperty("class", "SecondaryBtn")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._save_as)

        btn_row.addWidget(self.btn_gen)
        btn_row.addWidget(self.btn_open)
        btn_row.addWidget(self.btn_save)

        card_layout.addLayout(btn_row)

        disc = QLabel(
            "MANDATORY BIOMEDICAL DISCLAIMER:\n"
            "This prototype analyses synthetic EEG-like signals for demonstration and development purposes. "
            "The results are not a medical diagnosis or validated assessment of a person's neurological condition."
        )
        disc.setStyleSheet("font-size: 10px; font-style: italic; color: #EF4444; border: 1px solid #EF4444; border-radius: 8px; padding: 10px; background-color: rgba(239, 68, 68, 0.1);")
        card_layout.addWidget(disc)

        layout.addWidget(card)
        layout.addStretch()

    def set_session(self, sess_data: dict):
        self.current_session_data = sess_data
        self.status_lbl.setText(f"Session Loaded: {sess_data.get('session_id', 'SESS-1001')}")

    def _do_generate(self):
        if not self.current_session_data:
            self.current_session_data = {
                'session_id': 'SESS-1001',
                'timestamp': '2026-07-28 10:00:00',
                'duration': 272.0,
                'sampling_rate': 250,
                'mode': 'SIMULATION',
                'rel_delta': 13.5,
                'rel_theta': 24.2,
                'rel_alpha': 38.4,
                'rel_beta': 23.9,
                'dominant_band': 'ALPHA',
                'cognitive_state': 'MODERATE',
                'stress_index': 0.48,
                'confidence': 88.5
            }

        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "reports")
        os.makedirs(output_dir, exist_ok=True)
        pdf_name = f"NeuroSim_Report_{self.current_session_data.get('session_id', 'SESS')}.pdf"
        output_path = os.path.join(output_dir, pdf_name)

        try:
            PDFReportGenerator.generate_report(self.current_session_data, output_path)
            self.last_pdf_path = output_path
            self.status_lbl.setText(f"SUCCESS: Report Generated at {output_path}")
            self.btn_open.setEnabled(True)
            self.btn_save.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "PDF Error", f"Failed to generate PDF report: {e}")

    def _open_pdf(self):
        if self.last_pdf_path and os.path.exists(self.last_pdf_path):
            try:
                os.startfile(self.last_pdf_path)
            except Exception as e:
                subprocess.Popen([self.last_pdf_path], shell=True)

    def _save_as(self):
        if self.last_pdf_path and os.path.exists(self.last_pdf_path):
            dest, _ = QFileDialog.getSaveFileName(self, "Save Report", "NeuroSim_Analysis_Report.pdf", "PDF Files (*.pdf)")
            if dest:
                import shutil
                shutil.copyfile(self.last_pdf_path, dest)
                QMessageBox.information(self, "Saved", f"Report saved to {dest}")
