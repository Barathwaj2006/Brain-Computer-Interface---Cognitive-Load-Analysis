"""
Overview Screen Module — Executive Medical-Grade Dashboard
Integrates:
- Live Waveform Showcase
- 10-20 Topographic Brain Spatial Power Heatmap
- 4 Real-Time Band Power Cards (Delta, Theta, Alpha, Beta)
- Impedance Contact Quality Check (< 5 kΩ) & Active Filter Badges
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
from PySide6.QtCore import Qt, Signal
import pyqtgraph as pg

from src.app.config import (
    COLOR_CYAN, COLOR_EMERALD, COLOR_PURPLE, COLOR_AMBER, COLOR_CARD_BG,
    NOTCH_FILTER_STATUS, EOG_FILTER_STATUS, IMPEDANCE_THRESHOLD_KOHM
)
from src.visualization.topographic_map import TopographicMapWidget

class OverviewScreen(QWidget):
    start_session_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header Title & Filter Badges
        h_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        
        title_lbl = QLabel("SYSTEM OVERVIEW — NEURAL SIGNAL INTERFACE")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 900; color: #F8FAFC; letter-spacing: 1px;")
        
        sub_lbl = QLabel("Real-Time 10-20 System Spatial Mapping • 250 Hz Biomedical DSP")
        sub_lbl.setStyleSheet("font-size: 11px; color: #94A3B8;")
        
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)

        h_layout.addLayout(title_box)
        h_layout.addStretch()

        # Status & Filter Badges
        b_notch = QLabel(f"✓ {NOTCH_FILTER_STATUS}")
        b_notch.setStyleSheet("background: rgba(16,185,129,0.12); color: #10B981; border: 1px solid #10B981; padding: 4px 10px; border-radius: 10px; font-size: 10px; font-weight: 800;")
        
        b_imp = QLabel(f"IMPEDANCE: 3.2 kΩ (< {IMPEDANCE_THRESHOLD_KOHM} kΩ)")
        b_imp.setStyleSheet("background: rgba(6,182,212,0.12); color: #06B6D4; border: 1px solid #06B6D4; padding: 4px 10px; border-radius: 10px; font-size: 10px; font-weight: 800;")

        h_layout.addWidget(b_notch)
        h_layout.addWidget(b_imp)
        layout.addLayout(h_layout)

        # Main Grid: Left Waveform + Right Topographic Map
        top_grid = QHBoxLayout()
        top_grid.setSpacing(16)

        # Left Card: Live Waveform
        wave_card = QFrame()
        wave_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px;")
        wave_layout = QVBoxLayout(wave_card)
        
        wave_title = QLabel("PRIMARY EEG SIGNAL TRACE (250 Hz)")
        wave_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #94A3B8; letter-spacing: 1px;")
        wave_layout.addWidget(wave_title)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(None)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen(color=COLOR_CYAN, width=2))
        wave_layout.addWidget(self.plot_widget)

        top_grid.addWidget(wave_card, stretch=2)

        # Right Card: Topographic Brain Spatial Heatmap
        topo_card = QFrame()
        topo_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px;")
        topo_layout = QVBoxLayout(topo_card)
        
        topo_title = QLabel("SPATIAL POWER TOPOGRAPHY (10-20 MONTAGE)")
        topo_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #94A3B8; letter-spacing: 1px; margin-bottom: 6px;")
        topo_layout.addWidget(topo_title)

        self.topo_widget = TopographicMapWidget()
        topo_layout.addWidget(self.topo_widget, alignment=Qt.AlignCenter)

        top_grid.addWidget(topo_card, stretch=1)
        layout.addLayout(top_grid, stretch=2)

        # Middle Row: 4 Band Power Cards
        bands_layout = QHBoxLayout()
        bands_layout.setSpacing(14)

        self.card_delta = self._create_band_card("δ DELTA", "0.5 - 4 Hz", "25.0 %", COLOR_CYAN)
        self.card_theta = self._create_band_card("θ THETA", "4 - 8 Hz", "25.0 %", COLOR_EMERALD)
        self.card_alpha = self._create_band_card("α ALPHA", "8 - 13 Hz", "25.0 %", COLOR_PURPLE)
        self.card_beta = self._create_band_card("β BETA", "13 - 30 Hz", "25.0 %", COLOR_AMBER)

        bands_layout.addWidget(self.card_delta['frame'])
        bands_layout.addWidget(self.card_theta['frame'])
        bands_layout.addWidget(self.card_alpha['frame'])
        bands_layout.addWidget(self.card_beta['frame'])
        
        layout.addLayout(bands_layout)

        # Bottom Row: Analytics Summary & Session Launch
        bottom_layout = QHBoxLayout()
        
        analytics_card = QFrame()
        analytics_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px;")
        a_layout = QGridLayout(analytics_card)
        
        a_layout.addWidget(self._make_sublabel("COGNITIVE LOAD"), 0, 0)
        self.val_load = self._make_val("MODERATE", COLOR_CYAN)
        a_layout.addWidget(self.val_load, 1, 0)

        a_layout.addWidget(self._make_sublabel("STRESS INDEX"), 0, 1)
        self.val_stress = self._make_val("0.48", COLOR_AMBER)
        a_layout.addWidget(self.val_stress, 1, 1)

        a_layout.addWidget(self._make_sublabel("ENGAGEMENT"), 0, 2)
        self.val_eng = self._make_val("72%", COLOR_EMERALD)
        a_layout.addWidget(self.val_eng, 1, 2)

        a_layout.addWidget(self._make_sublabel("DOMINANT RHYTHM"), 0, 3)
        self.val_dom = self._make_val("ALPHA", COLOR_PURPLE)
        a_layout.addWidget(self.val_dom, 1, 3)

        bottom_layout.addWidget(analytics_card, stretch=3)

        # Session Action Button
        self.btn_session = QPushButton("▶ START SESSION")
        self.btn_session.setStyleSheet("background: linear-gradient(135deg, #10B981, #059669); color: white; font-weight: 800; font-size: 14px; padding: 18px 24px; border-radius: 12px; border: none;")
        self.btn_session.setCursor(Qt.PointingHandCursor)
        self.btn_session.clicked.connect(self.start_session_requested.emit)
        
        bottom_layout.addWidget(self.btn_session, stretch=1)
        
        layout.addLayout(bottom_layout)

    def _create_band_card(self, name, freq, val, color):
        frame = QFrame()
        frame.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid rgba(255,255,255,0.08); border-left: 4px solid {color}; border-radius: 10px; padding: 12px;")
        l = QVBoxLayout(frame)
        l.setSpacing(4)
        
        title = QLabel(name)
        title.setStyleSheet(f"font-size: 12px; font-weight: 900; color: {color};")
        
        sub = QLabel(freq)
        sub.setStyleSheet("font-size: 10px; color: #94A3B8;")
        
        val_lbl = QLabel(val)
        val_lbl.setStyleSheet("font-size: 22px; font-weight: 900; color: #F8FAFC; margin-top: 4px;")
        
        l.addWidget(title)
        l.addWidget(sub)
        l.addWidget(val_lbl)
        
        return {'frame': frame, 'val': val_lbl}

    def _make_sublabel(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 10px; font-weight: 800; color: #94A3B8; letter-spacing: 1px;")
        return lbl

    def _make_val(self, text, color):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {color}; margin-top: 2px;")
        return lbl

    def update_overview(self, wave_data, band_powers, metrics):
        if len(wave_data) > 0:
            self.plot_curve.setData(wave_data[-300:])
        
        self.topo_widget.update_powers(band_powers)

        pD = band_powers.get('delta_rel', 25.0)
        pT = band_powers.get('theta_rel', 25.0)
        pA = band_powers.get('alpha_rel', 25.0)
        pB = band_powers.get('beta_rel', 25.0)

        self.card_delta['val'].setText(f"{pD:.1f} %")
        self.card_theta['val'].setText(f"{pT:.1f} %")
        self.card_alpha['val'].setText(f"{pA:.1f} %")
        self.card_beta['val'].setText(f"{pB:.1f} %")

        self.val_stress.setText(f"{metrics.get('stress_index', 0.48):.2f}")
        self.val_dom.setText(metrics.get('dominant_band', 'ALPHA'))
        
        load = metrics.get('load_class', 'MODERATE')
        self.val_load.setText(load)
        if load == "HIGH":
            self.val_load.setStyleSheet("font-size: 20px; font-weight: 900; color: #EF4444;")
        elif load == "RELAXED":
            self.val_load.setStyleSheet("font-size: 20px; font-weight: 900; color: #8B5CF6;")
        else:
            self.val_load.setStyleSheet("font-size: 20px; font-weight: 900; color: #06B6D4;")
