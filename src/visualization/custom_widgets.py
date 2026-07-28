"""
Custom PySide6 Graphical Widgets & Biomedical Components
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QFont
from src.app.config import COLORS

class GlassCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "GlassCard")

class StatusBadge(QFrame):
    def __init__(self, text: str = "DISCONNECTED", is_active: bool = False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        
        self.dot = QLabel("●")
        self.label = QLabel(text)
        self.label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        
        layout.addWidget(self.dot)
        layout.addWidget(self.label)
        
        self.set_status(text, is_active)

    def set_status(self, text: str, is_active: bool):
        self.label.setText(text)
        if is_active:
            self.dot.setStyleSheet(f"color: {COLORS['accent_emerald']}; font-size: 12px;")
            self.setStyleSheet(f"background-color: rgba(16, 185, 129, 0.15); border: 1px solid {COLORS['accent_emerald']}; border-radius: 12px;")
            self.label.setStyleSheet(f"color: {COLORS['accent_emerald']};")
        else:
            self.dot.setStyleSheet(f"color: {COLORS['accent_rose']}; font-size: 12px;")
            self.setStyleSheet(f"background-color: rgba(239, 68, 68, 0.15); border: 1px solid {COLORS['accent_rose']}; border-radius: 12px;")
            self.label.setStyleSheet(f"color: {COLORS['accent_rose']};")

class MetricCard(GlassCard):
    def __init__(self, title: str, value: str = "0.0", unit: str = "", subtitle: str = "", accent_color: str = "#06B6D4", parent=None):
        super().__init__(parent)
        self.accent_color = accent_color
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        
        self.value_lbl = QLabel(f"{value} {unit}".strip())
        self.value_lbl.setStyleSheet(f"color: {accent_color}; font-size: 22px; font-weight: bold;")
        
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.value_lbl)
        layout.addWidget(self.sub_lbl)

    def update_value(self, value: str, unit: str = "", subtitle: str = None):
        self.value_lbl.setText(f"{value} {unit}".strip())
        if subtitle:
            self.sub_lbl.setText(subtitle)

class BandPowerBar(QFrame):
    def __init__(self, band_name: str, freq_range: str, color_hex: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 8)
        layout.setSpacing(4)

        header_layout = QHBoxLayout()
        self.name_lbl = QLabel(f"{band_name.upper()} ({freq_range})")
        self.name_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #F8FAFC;")
        
        self.val_lbl = QLabel("0.0 %")
        self.val_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {color_hex};")
        
        header_layout.addWidget(self.name_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.val_lbl)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(25)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #0F172A;
                border-radius: 4px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {color_hex};
                border-radius: 4px;
            }}
        """)

        layout.addLayout(header_layout)
        layout.addWidget(self.bar)

    def set_percentage(self, pct: float):
        val = int(max(0.0, min(100.0, pct)))
        self.bar.setValue(val)
        self.val_lbl.setText(f"{pct:.1f} %")
