"""
Radial Clinical Stress Index Gauge Component
Custom PySide6 QPainter gauge displaying Spectral Stress Index with color gradient arcs.
"""

import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QConicalGradient, QFont
from src.app.config import COLORS

class ClinicalStressGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 180)
        self.stress_value = 0.5  # 0.0 to 2.0+

    def set_stress_index(self, val: float):
        self.stress_value = max(0.0, min(2.5, float(val)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        radius = min(w, h) * 0.4

        rect = QRectF(cx - radius, cy - radius, radius * 2.0, radius * 2.0)

        # Draw Background Track Arc (225 deg to -45 deg)
        start_angle = 225 * 16
        span_angle = -270 * 16

        pen_bg = QPen(QColor(30, 41, 59), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, start_angle, span_angle)

        # Draw Colored Value Arc
        pct = min(1.0, self.stress_value / 2.0)
        value_span = int(-270 * 16 * pct)

        if pct < 0.35:
            arc_color = QColor(COLORS['accent_emerald'])
        elif pct < 0.70:
            arc_color = QColor(COLORS['accent_amber'])
        else:
            arc_color = QColor(COLORS['accent_rose'])

        pen_val = QPen(arc_color, 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_val)
        painter.drawArc(rect, start_angle, value_span)

        # Draw Text Value in Center
        painter.setPen(QColor(COLORS['text_primary']))
        font_val = QFont("Segoe UI", 18, QFont.Weight.Bold)
        painter.setFont(font_val)
        painter.drawText(QRectF(cx - 50, cy - 22, 100, 30), Qt.AlignmentFlag.AlignCenter, f"{self.stress_value:.2f}")

        painter.setPen(QColor(COLORS['text_muted']))
        font_sub = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font_sub)
        painter.drawText(QRectF(cx - 60, cy + 8, 120, 20), Qt.AlignmentFlag.AlignCenter, "STRESS INDEX")
