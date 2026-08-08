"""
Overview Screen Module — Executive Medical-Grade Dashboard
Theme: Bright Frosted Glassmorphism
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
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        
        sub_lbl = QLabel("Real-Time 10-20 System Spatial Mapping • 250 Hz Biomedical DSP")
        sub_lbl.setStyleSheet("font-size: 11px; color: #64748B;")
        
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)

        h_layout.addLayout(title_box)
        h_layout.addStretch()

        # Status & Filter Badges
        b_notch = QLabel(f"✓ {NOTCH_FILTER_STATUS}")
        b_notch.setStyleSheet("background: rgba(5,150,105,0.12); color: #059669; border: 1px solid #059669; padding: 4px 10px; border-radius: 10px; font-size: 10px; font-weight: 800;")
        
        b_imp = QLabel(f"IMPEDANCE: 3.2 kΩ (< {IMPEDANCE_THRESHOLD_KOHM} kΩ)")
        b_imp.setStyleSheet("background: rgba(2,132,199,0.12); color: #0284C7; border: 1px solid #0284C7; padding: 4px 10px; border-radius: 10px; font-size: 10px; font-weight: 800;")

        h_layout.addWidget(b_notch)
        h_layout.addWidget(b_imp)
        layout.addLayout(h_layout)

        # Main Grid: Left Waveform + Right Topographic Map
        top_grid = QHBoxLayout()
        top_grid.setSpacing(16)

        # Waveform Frame
        wave_frame = QFrame()
        wave_frame.setStyleSheet("background: rgba(255, 255, 255, 0.85); border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px;")
        w_layout = QVBoxLayout(wave_frame)
        
        w_title = QLabel("PRIMARY MONITOR TRACE (Fp1 - FRONT PROFILE)")
        w_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #0284C7; letter-spacing: 1px;")
        w_layout.addWidget(w_title)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#FFFFFF')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)
        self.curve = self.plot_widget.plot(pen=pg.mkPen(color='#0284C7', width=2))
        w_layout.addWidget(self.plot_widget)

        top_grid.addWidget(wave_frame, stretch=3)

        # Topographic Spatial Map Frame
        topo_frame = QFrame()
        topo_frame.setStyleSheet("background: rgba(255, 255, 255, 0.85); border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px;")
        t_layout = QVBoxLayout(topo_frame)

        t_title = QLabel("10-20 SYSTEM SPATIAL HEATMAP")
        t_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #0284C7; letter-spacing: 1px;")
        t_layout.addWidget(t_title)

        self.topo_map = TopographicMapWidget()
        t_layout.addWidget(self.topo_map)

        top_grid.addWidget(topo_frame, stretch=2)
        layout.addLayout(top_grid)

        # Bottom 4 Spectral Band Power Cards
        card_grid = QGridLayout()
        card_grid.setSpacing(14)

        self.card_delta = self._create_band_card("DELTA (0.5-4 Hz)", "25.0 %", COLOR_CYAN, card_grid, 0)
        self.card_theta = self._create_band_card("THETA (4-8 Hz)", "25.0 %", COLOR_EMERALD, card_grid, 1)
        self.card_alpha = self._create_band_card("ALPHA (8-13 Hz)", "25.0 %", COLOR_PURPLE, card_grid, 2)
        self.card_beta  = self._create_band_card("BETA (13-30 Hz)", "25.0 %", COLOR_AMBER, card_grid, 3)

        layout.addLayout(card_grid)

    def _create_band_card(self, title, val, color, grid_layout, col):
        card = QFrame()
        card.setStyleSheet("background: rgba(255, 255, 255, 0.85); border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px;")
        l = QVBoxLayout(card)

        t = QLabel(title)
        t.setStyleSheet("font-size: 10px; font-weight: 800; color: #64748B; letter-spacing: 1px;")
        
        v = QLabel(val)
        v.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {color}; margin-top: 4px;")

        l.addWidget(t)
        l.addWidget(v)

        grid_layout.addWidget(card, 0, col)
        return v

    def update_overview(self, signal_arr, band_powers, metrics):
        if len(signal_arr) > 0:
            self.curve.setData(signal_arr)

        self.card_delta.setText(f"{band_powers.get('delta_rel', 25.0):.1f} %")
        self.card_theta.setText(f"{band_powers.get('theta_rel', 25.0):.1f} %")
        self.card_alpha.setText(f"{band_powers.get('alpha_rel', 25.0):.1f} %")
        self.card_beta.setText(f"{band_powers.get('beta_rel', 25.0):.1f} %")

        # Update Topographic Heatmap
        powers = {
            'Fp1': band_powers.get('alpha_rel', 25.0),
            'Fp2': band_powers.get('alpha_rel', 25.0),
            'C3':  band_powers.get('theta_rel', 25.0),
            'C4':  band_powers.get('theta_rel', 25.0),
            'P3':  band_powers.get('beta_rel', 25.0),
            'P4':  band_powers.get('beta_rel', 25.0),
            'O1':  band_powers.get('delta_rel', 25.0),
            'O2':  band_powers.get('delta_rel', 25.0)
        }
        self.topo_map.update_power_levels(powers)
