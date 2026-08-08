"""
Experiment Mode Screen Module
Allows running structured research experiments:
- Baseline Recording
- Alpha Dominance Relaxation Test
- Beta Dominance Focus Test
- Cognitive Load Simulation
Theme: Bright Frosted Glassmorphism
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QGridLayout
from PySide6.QtCore import Qt, Signal
from src.app.config import COLOR_CARD_BG, COLOR_CYAN

class ExperimentScreen(QWidget):
    experiment_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title_lbl = QLabel("EXPERIMENTAL PROTOCOLS — RESEARCH SIMULATION")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        layout.addWidget(title_lbl)

        grid_card = QFrame()
        grid_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px;")
        g_layout = QGridLayout(grid_card)
        g_layout.setSpacing(16)

        experiments = [
            ("1. BASELINE PROTOCOL", "Equally distributed spectrum profile across all frequency bands.", "baseline"),
            ("2. ALPHA DOMINANCE TEST", "Simulates relaxed alertness with 10 Hz Alpha power peak.", "alpha"),
            ("3. BETA DOMINANCE TEST", "Simulates high cognitive workload with 20 Hz Beta power peak.", "beta"),
            ("4. THETA FATIGUE PROTOCOL", "Simulates drowsiness and mental fatigue with 6 Hz Theta power peak.", "theta")
        ]

        for i, (exp_title, exp_desc, exp_key) in enumerate(experiments):
            row = i // 2
            col = i % 2

            frame = QFrame()
            frame.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 16px;")
            fl = QVBoxLayout(frame)

            t = QLabel(exp_title)
            t.setStyleSheet(f"font-size: 13px; font-weight: 900; color: {COLOR_CYAN};")
            
            d = QLabel(exp_desc)
            d.setStyleSheet("font-size: 11px; color: #64748B; margin: 6px 0;")
            d.setWordWrap(True)

            btn = QPushButton("▶ LAUNCH EXPERIMENT")
            btn.setStyleSheet("background: linear-gradient(135deg, #0284C7, #0369A1); color: white; font-weight: 800; font-size: 11px; padding: 10px; border-radius: 6px; border: none;")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, k=exp_key: self.experiment_selected.emit(k))

            fl.addWidget(t)
            fl.addWidget(d)
            fl.addWidget(btn)

            g_layout.addWidget(frame, row, col)

        layout.addWidget(grid_card)
