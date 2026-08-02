"""
Presentation Mode Screen Module
Fullscreen Expo demonstration mode for 3-minute judge presentations.
Focuses purely on high-impact visuals:
Live Signal -> Band Power Cards -> Cognitive Analytics -> AI Interpretation
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
from PySide6.QtCore import Qt, Signal
import pyqtgraph as pg
from src.app.config import COLOR_CARD_BG, COLOR_CYAN, COLOR_PURPLE, COLOR_EMERALD, COLOR_AMBER

class PresentationModeScreen(QWidget):
    exit_presentation = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        h_layout = QHBoxLayout()
        title_lbl = QLabel("◉╱╲◉ NEUROSIM — EXPO DEMONSTRATION MODE")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: 900; color: #06B6D4; letter-spacing: 2px;")
        
        btn_exit = QPushButton("✖ EXIT PRESENTATION")
        btn_exit.setStyleSheet("background: rgba(239,68,68,0.2); color: #EF4444; border: 1px solid #EF4444; font-weight: 800; font-size: 11px; padding: 8px 16px; border-radius: 8px;")
        btn_exit.setCursor(Qt.PointingHandCursor)
        btn_exit.clicked.connect(self.exit_presentation.emit)

        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        h_layout.addWidget(btn_exit)
        layout.addLayout(h_layout)

        # Live Waveform Showcase
        wave_card = QFrame()
        wave_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 2px solid rgba(6,182,212,0.4); border-radius: 16px; padding: 16px;")
        w_layout = QVBoxLayout(wave_card)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(None)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen(color=COLOR_CYAN, width=3))
        w_layout.addWidget(self.plot_widget)

        layout.addWidget(wave_card, stretch=3)

        # Analytics Bar
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)

        self.card_dom = self._make_card("DOMINANT RHYTHM", "ALPHA (10 Hz)", COLOR_PURPLE)
        self.card_load = self._make_card("COGNITIVE LOAD", "MODERATE", COLOR_CYAN)
        self.card_stress = self._make_card("STRESS INDEX", "0.48", COLOR_AMBER)
        self.card_qual = self._make_card("SIGNAL QUALITY", "EXCELLENT (250Hz)", COLOR_EMERALD)

        bottom_layout.addWidget(self.card_dom['frame'])
        bottom_layout.addWidget(self.card_load['frame'])
        bottom_layout.addWidget(self.card_stress['frame'])
        bottom_layout.addWidget(self.card_qual['frame'])

        layout.addLayout(bottom_layout, stretch=1)

    def _make_card(self, title, val, color):
        frame = QFrame()
        frame.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px;")
        l = QVBoxLayout(frame)
        
        t = QLabel(title)
        t.setStyleSheet("font-size: 10px; font-weight: 800; color: #94A3B8; letter-spacing: 1px;")
        
        v = QLabel(val)
        v.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {color}; margin-top: 4px;")

        l.addWidget(t)
        l.addWidget(v)

        return {'frame': frame, 'val': v}

    def update_presentation(self, wave_data, metrics):
        if len(wave_data) > 0:
            self.plot_curve.setData(wave_data[-400:])
        self.card_dom['val'].setText(metrics.get('dominant_band', 'ALPHA'))
        self.card_load['val'].setText(metrics.get('load_class', 'MODERATE'))
        self.card_stress['val'].setText(f"{metrics.get('stress_index', 0.48):.2f}")
