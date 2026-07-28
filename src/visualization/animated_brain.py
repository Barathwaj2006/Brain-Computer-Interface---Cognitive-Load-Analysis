"""
Animated Brain Canvas Component
High-end PySide6 QPainter custom widget rendering a pulsating neural mesh wave animation.
"""

import math
import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient
from src.app.config import COLORS

class AnimatedBrainCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self.phase = 0.0
        
        # 60 FPS animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)

    def update_animation(self):
        self.phase += 0.04
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        # Background radial glow
        rad_grad = QRadialGradient(cx, cy, max(w, h) / 2.0)
        rad_grad.setColorAt(0.0, QColor(6, 182, 212, 40))
        rad_grad.setColorAt(0.7, QColor(139, 92, 246, 15))
        rad_grad.setColorAt(1.0, QColor(11, 15, 25, 0))
        painter.fillRect(self.rect(), QBrush(rad_grad))

        # Outer pulsing neural rings
        pulse = math.sin(self.phase) * 6.0
        base_radius = min(w, h) * 0.32

        for i, color_hex in enumerate(['#06B6D4', '#8B5CF6', '#10B981']):
            r = base_radius + (i * 14.0) + pulse
            pen = QPen(QColor(color_hex), 1.5, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), r, r)

        # Neural node mesh points
        num_nodes = 12
        points = []
        for i in range(num_nodes):
            angle = (2.0 * math.pi / num_nodes) * i + (self.phase * 0.2)
            r_var = base_radius + math.sin(self.phase * 2.0 + i) * 10.0
            px = cx + r_var * math.cos(angle)
            py = cy + r_var * math.sin(angle)
            points.append((px, py))

        # Connecting synapse lines
        painter.setPen(QPen(QColor(6, 182, 212, 80), 1))
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                if (i + j) % 3 == 0:
                    painter.drawLine(QPointF(points[i][0], points[i][1]), QPointF(points[j][0], points[j][1]))

        # Render Glowing Nodes
        for px, py in points:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(6, 182, 212)))
            painter.drawEllipse(QPointF(px, py), 4, 4)

        # Central Glowing Core
        core_r = 18.0 + math.sin(self.phase * 1.5) * 3.0
        core_grad = QRadialGradient(cx, cy, core_r)
        core_grad.setColorAt(0.0, QColor(248, 250, 252, 230))
        core_grad.setColorAt(0.5, QColor(6, 182, 212, 180))
        core_grad.setColorAt(1.0, QColor(139, 92, 246, 0))
        painter.setBrush(QBrush(core_grad))
        painter.drawEllipse(QPointF(cx, cy), core_r, core_r)
