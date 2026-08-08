"""
System Architecture Screen Module
Renders interactive pipeline architecture diagram:
Signal Source -> 250 Hz Sampling -> Butterworth Filter -> Welch PSD -> Band Extraction -> Feature Engine -> Classifier -> AI Interpretation -> Session Report
Theme: Bright Frosted Glassmorphism
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
from PySide6.QtCore import Qt
from src.app.config import COLOR_CARD_BG, COLOR_CYAN

class ArchitectureScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title_lbl = QLabel("NEUROSIM PIPELINE ARCHITECTURE — SYSTEM FLOW")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        layout.addWidget(title_lbl)

        grid_card = QFrame()
        grid_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px;")
        g_layout = QGridLayout(grid_card)
        g_layout.setSpacing(16)

        blocks = [
            ("1. SIGNAL SOURCE", "Signal Simulator / NeuroSim Device", "Generates or captures time-series EEG waveforms."),
            ("2. SAMPLING ENGINE", "250 Hz Continuous Sampling", "Buffers 1250 samples per 5-second sliding window."),
            ("3. FILTERING STAGE", "Butterworth Bandpass (0.5 - 40 Hz)", "Removes DC offset, drift, and high-frequency noise."),
            ("4. FFT & WELCH PSD", "512 Point FFT Power Spectrum", "Transforms time-domain signal into frequency spectrum."),
            ("5. BAND EXTRACTION", "Delta, Theta, Alpha, Beta Ratios", "Integrates area under PSD curve for each frequency band."),
            ("6. FEATURE ENGINE", "Stress Index, TBR, ABR, Engagement", "Calculates clinical spectral metrics and ratios."),
            ("7. CLASSIFIER", "Random Forest ML & Rule Classifier", "Categorizes cognitive state into LOW / MODERATE / HIGH."),
            ("8. AI INTERPRETATION", "Deterministic Session Explanation", "Generates research narrative and result attribution."),
            ("9. SESSION REPORT", "ReportLab PDF & Database Record", "Stores session metrics in SQLite and generates PDF report.")
        ]

        for i, (b_title, b_sub, b_desc) in enumerate(blocks):
            row = i // 3
            col = i % 3
            block_frame = QFrame()
            block_frame.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px;")
            b_l = QVBoxLayout(block_frame)
            
            t = QLabel(b_title)
            t.setStyleSheet(f"font-size: 12px; font-weight: 900; color: {COLOR_CYAN};")
            
            s = QLabel(b_sub)
            s.setStyleSheet("font-size: 11px; font-weight: 700; color: #0F172A; margin-top: 2px;")
            
            d = QLabel(b_desc)
            d.setStyleSheet("font-size: 10px; color: #64748B; margin-top: 4px;")
            d.setWordWrap(True)

            b_l.addWidget(t)
            b_l.addWidget(s)
            b_l.addWidget(d)

            g_layout.addWidget(block_frame, row, col)

        layout.addWidget(grid_card)
