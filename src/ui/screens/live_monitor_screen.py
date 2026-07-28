"""
Screen 3 — Live Monitor Screen (MAIN MONITORING INTERFACE)
Real-time high-FPS PyQtGraph scrolling waveform, live PSD frequency spectrum, band power bars,
clinical stress index gauge, and synthetic cognitive load analysis card.
"""

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from src.app.config import COLORS, BAND_LIMITS
from src.visualization.custom_widgets import GlassCard, BandPowerBar, MetricCard
from src.visualization.stress_gauge import ClinicalStressGauge

class LiveMonitorScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Header bar
        header_layout = QHBoxLayout()
        header_title = QLabel("LIVE EEG MONITOR & SPECTRAL ANALYSIS")
        header_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        
        self.mode_badge = QLabel("SIMULATION MODE")
        self.mode_badge.setStyleSheet(f"background-color: rgba(6, 182, 212, 0.15); color: {COLORS['accent_cyan']}; font-weight: bold; border-radius: 8px; padding: 4px 12px;")

        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(self.mode_badge)
        layout.addLayout(header_layout)

        # Main Split Grid: Left = Waveform & PSD, Right = Band Analysis & Cognitive Card
        main_grid = QHBoxLayout()
        main_grid.setSpacing(14)

        # Left Column (Plots)
        left_col = QVBoxLayout()
        left_col.setSpacing(14)

        # 1. Live EEG Waveform Plot (PyQtGraph)
        plot_card = GlassCard()
        plot_layout = QVBoxLayout(plot_card)
        plot_layout.setContentsMargins(12, 12, 12, 12)

        plot_title = QLabel("LIVE EEG SIGNAL WAVEFORM (uV)")
        plot_title.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLORS['text_muted']}; letter-spacing: 1px;")
        plot_layout.addWidget(plot_title)

        pg.setConfigOptions(antialias=True)
        self.wave_plot = pg.PlotWidget()
        self.wave_plot.setBackground(COLORS['bg_card'])
        self.wave_plot.showGrid(x=True, y=True, alpha=0.2)
        self.wave_plot.setYRange(-100, 100)
        self.wave_curve = self.wave_plot.plot(pen=pg.mkPen(color=COLORS['accent_cyan'], width=2))
        
        # Fill under curve
        self.fill_item = pg.FillBetweenItem(
            self.wave_curve,
            self.wave_plot.plot(np.zeros(1250), pen=None),
            brush=pg.mkBrush(color=(6, 182, 212, 35))
        )
        self.wave_plot.addItem(self.fill_item)

        plot_layout.addWidget(self.wave_plot)
        left_col.addWidget(plot_card, stretch=3)

        # 2. Live PSD Frequency Spectrum Plot (0 - 40 Hz)
        psd_card = GlassCard()
        psd_layout = QVBoxLayout(psd_card)
        psd_layout.setContentsMargins(12, 12, 12, 12)

        psd_title = QLabel("POWER SPECTRAL DENSITY (PSD) — FREQUENCY SPECTRUM (0–40 Hz)")
        psd_title.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLORS['text_muted']}; letter-spacing: 1px;")
        psd_layout.addWidget(psd_title)

        self.psd_plot = pg.PlotWidget()
        self.psd_plot.setBackground(COLORS['bg_card'])
        self.psd_plot.showGrid(x=True, y=True, alpha=0.2)
        self.psd_plot.setXRange(0, 40)
        self.psd_curve = self.psd_plot.plot(pen=pg.mkPen(color=COLORS['accent_purple'], width=2))

        # Add region highlight shading for EEG bands
        self._add_band_regions()

        psd_layout.addWidget(self.psd_plot)
        left_col.addWidget(psd_card, stretch=2)

        main_grid.addLayout(left_col, stretch=6)

        # Right Column (Band Meters & Cognitive Card)
        right_col = QVBoxLayout()
        right_col.setSpacing(14)

        # 3. Real-time Band Power Progress Bars
        bars_card = GlassCard()
        bars_layout = QVBoxLayout(bars_card)
        bars_layout.setContentsMargins(16, 14, 16, 14)

        bars_title = QLabel("REAL-TIME BAND POWER DISTRIBUTION")
        bars_title.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLORS['text_muted']}; letter-spacing: 1px;")
        bars_layout.addWidget(bars_title)

        self.bar_delta = BandPowerBar("DELTA (δ)", "0.5 - 4 Hz", COLORS['accent_cyan'])
        self.bar_theta = BandPowerBar("THETA (θ)", "4 - 8 Hz", COLORS['accent_emerald'])
        self.bar_alpha = BandPowerBar("ALPHA (α)", "8 - 13 Hz", COLORS['accent_purple'])
        self.bar_beta  = BandPowerBar("BETA (β)",  "13 - 30 Hz", COLORS['accent_amber'])

        bars_layout.addWidget(self.bar_delta)
        bars_layout.addWidget(self.bar_theta)
        bars_layout.addWidget(self.bar_alpha)
        bars_layout.addWidget(self.bar_beta)

        right_col.addWidget(bars_card)

        # 4. Cognitive Load & Stress Analysis Card
        cog_card = GlassCard()
        cog_layout = QVBoxLayout(cog_card)
        cog_layout.setContentsMargins(16, 14, 16, 14)

        cog_title = QLabel("CURRENT SYNTHETIC PATTERN ANALYSIS")
        cog_title.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLORS['text_muted']}; letter-spacing: 1px;")
        cog_layout.addWidget(cog_title)

        # Stress Gauge & Metrics Row
        gauge_row = QHBoxLayout()
        self.stress_gauge = ClinicalStressGauge(self)
        gauge_row.addWidget(self.stress_gauge, alignment=Qt.AlignmentFlag.AlignCenter)

        metrics_grid = QGridLayout()
        self.lbl_cog_load = QLabel("MODERATE")
        self.lbl_cog_load.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['accent_cyan']};")
        
        self.lbl_dom_band = QLabel("ALPHA (10.0 Hz)")
        self.lbl_dom_band.setStyleSheet("font-size: 13px; font-weight: bold; color: #F8FAFC;")
        
        self.lbl_conf = QLabel("85.0 %")
        self.lbl_conf.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLORS['accent_emerald']};")
        
        self.lbl_quality = QLabel("EXCELLENT")
        self.lbl_quality.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLORS['accent_emerald']};")

        metrics_grid.addWidget(QLabel("Cognitive Load:"), 0, 0)
        metrics_grid.addWidget(self.lbl_cog_load, 0, 1)
        metrics_grid.addWidget(QLabel("Dominant Band:"), 1, 0)
        metrics_grid.addWidget(self.lbl_dom_band, 1, 1)
        metrics_grid.addWidget(QLabel("Confidence:"), 2, 0)
        metrics_grid.addWidget(self.lbl_conf, 2, 1)
        metrics_grid.addWidget(QLabel("Signal Quality:"), 3, 0)
        metrics_grid.addWidget(self.lbl_quality, 3, 1)

        gauge_row.addLayout(metrics_grid)
        cog_layout.addLayout(gauge_row)

        # Mandatory Synthetic EEG Disclaimer
        disc = QLabel("SYNTHETIC EEG ANALYSIS — Demonstrational biomedical prototype. Not for clinical diagnosis.")
        disc.setStyleSheet("font-size: 9px; font-style: italic; color: #EF4444; border-top: 1px solid #1E293B; padding-top: 6px;")
        cog_layout.addWidget(disc)

        right_col.addWidget(cog_card)
        main_grid.addLayout(right_col, stretch=4)

        layout.addLayout(main_grid)

    def _add_band_regions(self):
        """Add shaded background regions for Delta, Theta, Alpha, Beta on PSD graph."""
        region_colors = {
            'delta': (6, 182, 212, 30),
            'theta': (16, 185, 129, 30),
            'alpha': (139, 92, 246, 30),
            'beta':  (245, 158, 11, 30)
        }
        for band, (low, high) in BAND_LIMITS.items():
            if band in region_colors:
                lr = pg.LinearRegionItem([low, high], movable=False, brush=region_colors[band])
                self.psd_plot.addItem(lr)

    def update_live_data(self, waveform: np.ndarray, freqs: np.ndarray, psd: np.ndarray, psd_metrics: dict, class_res: dict):
        """Update live UI plots and metrics continuously."""
        # 1. Update Waveform Plot
        if len(waveform) > 0:
            self.wave_curve.setData(waveform)

        # 2. Update PSD Plot
        if len(freqs) > 0 and len(psd) > 0:
            self.psd_curve.setData(freqs, psd)

        # 3. Update Band Bars
        rel = psd_metrics.get('rel_powers', {})
        self.bar_delta.set_percentage(rel.get('delta', 25.0))
        self.bar_theta.set_percentage(rel.get('theta', 25.0))
        self.bar_alpha.set_percentage(rel.get('alpha', 25.0))
        self.bar_beta.set_percentage(rel.get('beta', 25.0))

        # 4. Update Cognitive Load & Stress Index
        state = class_res.get('cognitive_state', 'MODERATE')
        self.lbl_cog_load.setText(state)
        if state == 'HIGH':
            self.lbl_cog_load.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['accent_rose']};")
        elif state == 'MODERATE':
            self.lbl_cog_load.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['accent_cyan']};")
        else:
            self.lbl_cog_load.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['accent_emerald']};")

        dom_band = psd_metrics.get('dominant_band', 'ALPHA')
        dom_freq = psd_metrics.get('dominant_freq', 10.0)
        self.lbl_dom_band.setText(f"{dom_band} ({dom_freq:.1f} Hz)")

        conf = class_res.get('confidence', 85.0)
        self.lbl_conf.setText(f"{conf:.1f} %")

        qual = class_res.get('signal_quality', 'EXCELLENT')
        self.lbl_quality.setText(qual)

        stress_idx = psd_metrics.get('stress_index', 0.5)
        self.stress_gauge.set_stress_index(stress_idx)
