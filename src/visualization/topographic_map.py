"""
Topographic Brain Heatmap Module
Custom QPainter 2D widget displaying 10-20 International System electrode positions
(Fp1, Fp2, C3, C4, P3, P4, O1, O2) and spatial spectral power density gradients.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QFont
from PySide6.QtCore import Qt, QPointF
from src.app.config import COLOR_CYAN, COLOR_EMERALD, COLOR_PURPLE, COLOR_AMBER

class TopographicMapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self.band_powers = {'delta_rel': 25.0, 'theta_rel': 25.0, 'alpha_rel': 25.0, 'beta_rel': 25.0}

    def update_powers(self, band_powers):
        self.band_powers = band_powers
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        r = min(w, h) * 0.40

        # Background Head Contour (Circle + Nose + Ears)
        pen_head = QPen(QColor(148, 163, 184, 120), 2)
        painter.setPen(pen_head)
        painter.setBrush(QColor(15, 23, 42, 200))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # Nose
        painter.drawLine(int(cx - 8), int(cy - r), int(cx), int(cy - r - 12))
        painter.drawLine(int(cx + 8), int(cy - r), int(cx), int(cy - r - 12))

        # Ears
        painter.drawArc(int(cx - r - 8), int(cy - 12), 12, 24, 90 * 16, 180 * 16)
        painter.drawArc(int(cx + r - 4), int(cy - 12), 12, 24, -90 * 16, 180 * 16)

        # 8 Electrode Coordinates (10-20 System)
        # Fp1, Fp2 (Frontal), C3, C4 (Central), P3, P4 (Parietal), O1, O2 (Occipital)
        electrodes = [
            ("Fp1", cx - r * 0.35, cy - r * 0.65, self.band_powers.get('beta_rel', 25.0), COLOR_AMBER),
            ("Fp2", cx + r * 0.35, cy - r * 0.65, self.band_powers.get('beta_rel', 25.0), COLOR_AMBER),
            ("C3",  cx - r * 0.60, cy,           self.band_powers.get('alpha_rel', 25.0), COLOR_PURPLE),
            ("C4",  cx + r * 0.60, cy,           self.band_powers.get('alpha_rel', 25.0), COLOR_PURPLE),
            ("P3",  cx - r * 0.40, cy + r * 0.50, self.band_powers.get('theta_rel', 25.0), COLOR_EMERALD),
            ("P4",  cx + r * 0.40, cy + r * 0.50, self.band_powers.get('theta_rel', 25.0), COLOR_EMERALD),
            ("O1",  cx - r * 0.20, cy + r * 0.80, self.band_powers.get('delta_rel', 25.0), COLOR_CYAN),
            ("O2",  cx + r * 0.20, cy + r * 0.80, self.band_powers.get('delta_rel', 25.0), COLOR_CYAN),
        ]

        # Draw Heatmap Gradients & Electrode Nodes
        font = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font)

        for name, ex, ey, power, hex_color in electrodes:
            # Heatmap Glow Gradient
            radial = QRadialGradient(QPointF(ex, ey), 32)
            c = QColor(hex_color)
            alpha_val = int(min(220, max(40, power * 4.5)))
            radial.setColorAt(0.0, QColor(c.red(), c.green(), c.blue(), alpha_val))
            radial.setColorAt(1.0, QColor(c.red(), c.green(), c.blue(), 0))
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(radial))
            painter.drawEllipse(QPointF(ex, ey), 32, 32)

            # Node Center Circle
            painter.setPen(QPen(QColor(248, 250, 252), 1.5))
            painter.setBrush(QColor(15, 23, 42))
            painter.drawEllipse(QPointF(ex, ey), 6, 6)

            # Label
            painter.setPen(QColor(248, 250, 252))
            painter.drawText(int(ex - 12), int(ey - 10), 24, 12, Qt.AlignCenter, name)
