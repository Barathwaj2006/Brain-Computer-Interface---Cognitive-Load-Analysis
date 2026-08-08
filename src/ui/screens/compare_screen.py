"""
Session Comparison Screen Module
Compares Session A vs Session B spectral band metrics and cognitive load classifications.
Theme: Bright Frosted Glassmorphism
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
from src.app.config import COLOR_CARD_BG, COLOR_CYAN

class CompareScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title_lbl = QLabel("SESSION COMPARISON MATRIX — SESSION A vs SESSION B")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        layout.addWidget(title_lbl)

        card = QFrame()
        card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px;")
        c_layout = QVBoxLayout(card)

        self.table = QTableWidget(6, 4)
        self.table.setHorizontalHeaderLabels(["Analytical Metric", "Session A (Baseline)", "Session B (Experimental)", "Variance Delta"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background: #FFFFFF; border: 1px solid #E2E8F0; gridline-color: #E2E8F0; color: #0F172A; font-size: 12px; border-radius: 8px; }
            QHeaderView::section { background: #F8FAFC; color: #475569; font-weight: 800; font-size: 11px; padding: 8px; border: none; border-bottom: 1px solid #E2E8F0; }
        """)

        metrics = [
            ("Delta Power (0.5-4 Hz)", "25.0 %", "14.2 %", "-10.8 %"),
            ("Theta Power (4-8 Hz)", "25.0 %", "21.7 %", "-3.3 %"),
            ("Alpha Power (8-13 Hz)", "25.0 %", "39.8 %", "+14.8 %"),
            ("Beta Power (13-30 Hz)", "25.0 %", "24.3 %", "-0.7 %"),
            ("Spectral Stress Index", "0.50", "0.39", "-0.11"),
            ("Cognitive Load State", "MODERATE", "RELAXED", "STATE SHIFT")
        ]

        for row, m in enumerate(metrics):
            for col, text in enumerate(m):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

        c_layout.addWidget(self.table)
        layout.addWidget(card)
