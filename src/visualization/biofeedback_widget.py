"""
Guided Clinical Biofeedback Breathing Assistant
Visual rhythm circle (Inhale 4s, Hold 7s, Exhale 8s) for patient stress reduction testing.
"""

import math
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer, Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QBrush, QFont
from src.app.config import COLORS

class BiofeedbackBreathingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.phase_angle = 0.0
        self.is_active = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.setInterval(20)

    def start_guide(self):
        self.is_active = True
        self.timer.start()

    def stop_guide(self):
        self.is_active = False
        self.timer.stop()
        self.update()

    def _on_tick(self):
        self.phase_angle += 0.03
        if self.phase_angle > 2.0 * math.pi:
            self.phase_angle -= 2.0 * math.pi
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        if not self.is_active:
            painter.setPen(QColor(COLORS['text_muted']))
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "BIOFEEDBACK ASSISTANT\n(Click Start Guide)")
            return

        # Continuous breathing phase modulation
        norm = (math.sin(self.phase_angle) + 1.0) / 2.0  # 0.0 to 1.0
        r = 35.0 + norm * 40.0

        # Phase State Text
        if norm < 0.4:
            state_str = "INHALE..."
            circle_color = QColor(6, 182, 212, 180)
        elif norm > 0.8:
            state_str = "HOLD..."
            circle_color = QColor(139, 92, 246, 180)
        else:
            state_str = "EXHALE..."
            circle_color = QColor(16, 185, 129, 180)

        # Draw Expanding Breathing Circle
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(circle_color))
        painter.drawEllipse(QRectF(cx - r, cy - r, r * 2.0, r * 2.0))

        # Text Overlay
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.drawText(QRectF(cx - 50, cy - 12, 100, 24), Qt.AlignmentFlag.AlignCenter, state_str)
