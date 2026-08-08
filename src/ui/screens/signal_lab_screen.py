"""
Signal Laboratory Screen Module
Allows researchers and faculty to inspect every stage of the 5-step DSP research pipeline:
Stage 1: Raw Signal Input (Line Plot)
Stage 2: Butterworth Filtered (Line Plot)
Stage 3: Welch PSD Spectrum (Frequency Plot 0-40 Hz)
Stage 4: Band Decomposition (Bar Graph)
Stage 5: Extracted Feature Vector (Table View)
Theme: Deep Charcoal Scientific Instrument Aesthetic
"""

import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QStackedWidget, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
import pyqtgraph as pg

from src.app.config import COLOR_CYAN, COLOR_EMERALD, COLOR_PURPLE, COLOR_AMBER, COLOR_CARD_BG, COLOR_BORDER, COLOR_TEXT_MUTED
from src.processing.filter import EEGFilter
from src.processing.psd import PSDAnalyzer

class SignalLabScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_obj = EEGFilter(sampling_rate=250)
        self.psd_analyzer = PSDAnalyzer(sampling_rate=250)
        self.current_stage = 0

        self.raw_data = np.array([])
        self.filtered_data = np.array([])
        self.freqs = np.array([])
        self.psd = np.array([])
        self.band_powers = {}
        self.metrics = {}

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Left Stage Navigation Menu
        nav_card = QFrame()
        nav_card.setFixedWidth(260)
        nav_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 16px;")
        n_layout = QVBoxLayout(nav_card)
        
        n_title = QLabel("DSP RESEARCH PIPELINE STAGES")
        n_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #0EA5E9; letter-spacing: 1px; margin-bottom: 8px;")
        n_layout.addWidget(n_title)

        self.stage_list = QListWidget()
        self.stage_list.setStyleSheet("""
            QListWidget { background: transparent; border: none; outline: none; }
            QListWidget::item { padding: 12px; border-radius: 6px; color: #9CA3AF; font-weight: 700; font-size: 12px; margin-bottom: 4px; }
            QListWidget::item:hover { background: rgba(14, 165, 233, 0.08); color: #F9FAFB; }
            QListWidget::item:selected { background: rgba(14, 165, 233, 0.15); color: #0EA5E9; font-weight: 900; }
        """)

        stages = [
            "1. Raw Composite Waveform",
            "2. Butterworth Filtered (0.5-40 Hz)",
            "3. Welch Power Spectral Density",
            "4. Spectral Band Integration",
            "5. Feature Vector & Classification"
        ]
        for s in stages:
            self.stage_list.addItem(QListWidgetItem(s))
        
        self.stage_list.setCurrentRow(0)
        self.stage_list.currentRowChanged.connect(self.switch_stage)
        n_layout.addWidget(self.stage_list)
        
        layout.addWidget(nav_card)

        # Right Stage Display Area
        display_card = QFrame()
        display_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 20px;")
        d_layout = QVBoxLayout(display_card)

        self.stage_title = QLabel("STAGE 1 — RAW COMPOSITE WAVEFORM")
        self.stage_title.setStyleSheet("font-size: 15px; font-weight: 900; color: #0EA5E9; letter-spacing: 1px;")
        d_layout.addWidget(self.stage_title)

        self.stage_desc = QLabel("Displays un-filtered composite waveform directly from signal generator or ESP32 hardware.")
        self.stage_desc.setStyleSheet("font-size: 11px; color: #9CA3AF; margin-bottom: 12px;")
        d_layout.addWidget(self.stage_desc)

        # Stacked Container for Different Stage Viewers
        self.stage_stack = QStackedWidget()

        # Viewer 0: Line Plot (Stages 1, 2, 3)
        self.line_plot_widget = pg.PlotWidget()
        self.line_plot_widget.setBackground("#0B0F19")
        self.line_plot_widget.showGrid(x=True, y=True, alpha=0.15)
        self.line_curve = self.line_plot_widget.plot(pen=pg.mkPen(color="#0EA5E9", width=2))
        self.stage_stack.addWidget(self.line_plot_widget)

        # Viewer 1: Bar Graph Plot (Stage 4 - Band Power)
        self.bar_plot_widget = pg.PlotWidget()
        self.bar_plot_widget.setBackground("#0B0F19")
        self.bar_plot_widget.showGrid(x=False, y=True, alpha=0.15)
        ax = self.bar_plot_widget.getAxis('bottom')
        ax.setTicks([[(1, "DELTA\n(0.5-4 Hz)"), (2, "THETA\n(4-8 Hz)"), (3, "ALPHA\n(8-13 Hz)"), (4, "BETA\n(13-30 Hz)")]])
        self.stage_stack.addWidget(self.bar_plot_widget)

        # Viewer 2: Feature Vector Table View (Stage 5)
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["Extracted Feature Metric", "Calculated Numerical Value"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.setStyleSheet("""
            QTableWidget {
                background-color: #0B0F19;
                gridline-color: #1F2937;
                border: 1px solid #1F2937;
                border-radius: 6px;
                color: #F9FAFB;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #1F2937;
                color: #0EA5E9;
                padding: 8px;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #374151;
            }
        """)
        self.stage_stack.addWidget(self.table_widget)

        d_layout.addWidget(self.stage_stack)
        layout.addWidget(display_card)

    def switch_stage(self, index):
        self.current_stage = index
        descriptions = [
            ("STAGE 1 — RAW COMPOSITE WAVEFORM", "Un-filtered composite waveform directly from simulator or ESP32 hardware (Time domain, uV)."),
            ("STAGE 2 — BUTTERWORTH BANDPASS FILTERED (0.5 - 40 Hz)", "Filtered time-series signal with DC offset and high-frequency muscle noise removed (Time domain, uV)."),
            ("STAGE 3 — WELCH POWER SPECTRAL DENSITY", "FFT power spectrum distribution (0-40 Hz) using 5-second overlapping Hann windows (Frequency domain, uV^2/Hz)."),
            ("STAGE 4 — SPECTRAL BAND POWER DECOMPOSITION", "Integrated relative power percentages across Delta, Theta, Alpha, and Beta frequency bands (Bar chart, 0-100%)."),
            ("STAGE 5 — EXTRACTED FEATURE VECTOR & METRICS", "Extracted clinical metrics (Stress Index, TBR, ABR, Peak Frequency) ready for dual model classification.")
        ]
        if 0 <= index < len(descriptions):
            self.stage_title.setText(descriptions[index][0])
            self.stage_desc.setText(descriptions[index][1])

        # Switch display stack based on stage type
        if index in [0, 1, 2]:
            self.stage_stack.setCurrentIndex(0)
            if index == 0:
                self.line_curve.setPen(pg.mkPen(color="#0EA5E9", width=2))
                self.line_plot_widget.setLabel('left', 'Voltage (uV)')
                self.line_plot_widget.setLabel('bottom', 'Time Samples')
            elif index == 1:
                self.line_curve.setPen(pg.mkPen(color="#10B981", width=2))
                self.line_plot_widget.setLabel('left', 'Filtered Voltage (uV)')
                self.line_plot_widget.setLabel('bottom', 'Time Samples')
            elif index == 2:
                self.line_curve.setPen(pg.mkPen(color="#8B5CF6", width=2))
                self.line_plot_widget.setLabel('left', 'Power Spectral Density (uV^2/Hz)')
                self.line_plot_widget.setLabel('bottom', 'Frequency (Hz)')
        elif index == 3:
            self.stage_stack.setCurrentIndex(1)
        elif index == 4:
            self.stage_stack.setCurrentIndex(2)

        # Force refresh viewer for new stage
        self.render_current_stage()

    def update_lab_data(self, wave_data, band_powers=None, metrics=None):
        if len(wave_data) < 32:
            return

        self.raw_data = np.array(wave_data)
        self.filtered_data = self.filter_obj.process(self.raw_data)
        self.freqs, self.psd = self.psd_analyzer.compute_psd(self.filtered_data)

        if band_powers:
            self.band_powers = band_powers
        else:
            self.band_powers = self.psd_analyzer.extract_band_powers(self.freqs, self.psd)

        if metrics:
            self.metrics = metrics
        else:
            self.metrics = self.psd_analyzer.compute_metrics(self.band_powers, self.freqs, self.psd)

        self.render_current_stage()

    def render_current_stage(self):
        if len(self.raw_data) == 0:
            return

        if self.current_stage == 0:
            self.line_curve.setData(self.raw_data[-400:])

        elif self.current_stage == 1:
            self.line_curve.setData(self.filtered_data[-400:])

        elif self.current_stage == 2:
            if len(self.freqs) > 0 and len(self.psd) > 0:
                idx = self.freqs <= 40.0
                self.line_curve.setData(self.freqs[idx], self.psd[idx])

        elif self.current_stage == 3:
            self.bar_plot_widget.clear()
            d = self.band_powers.get('delta_rel', 25.0)
            t = self.band_powers.get('theta_rel', 25.0)
            a = self.band_powers.get('alpha_rel', 25.0)
            b = self.band_powers.get('beta_rel', 25.0)

            bargraph = pg.BarGraphItem(
                x=[1, 2, 3, 4],
                height=[d, t, a, b],
                width=0.55,
                brushes=[
                    pg.mkBrush(14, 165, 233, 220),
                    pg.mkBrush(16, 185, 129, 220),
                    pg.mkBrush(139, 92, 246, 220),
                    pg.mkBrush(245, 158, 11, 220)
                ]
            )
            self.bar_plot_widget.addItem(bargraph)

        elif self.current_stage == 4:
            feature_rows = [
                ("Spectral Stress Index (Beta / (Alpha + Theta))", f"{self.metrics.get('stress_index', 0.5):.4f}"),
                ("Theta / Beta Ratio (TBR)", f"{self.metrics.get('tbr', 1.0):.4f}"),
                ("Alpha / Beta Ratio (ABR)", f"{self.metrics.get('abr', 1.0):.4f}"),
                ("Attentional Engagement Metric", f"{self.metrics.get('engagement', 0.5):.4f}"),
                ("Dominant Frequency Peak", f"{self.metrics.get('dominant_frequency', 10.0):.2f} Hz"),
                ("Dominant Frequency Band", f"{self.metrics.get('dominant_band', 'ALPHA')}"),
                ("Delta Band Relative Power", f"{self.band_powers.get('delta_rel', 25.0):.2f} %"),
                ("Theta Band Relative Power", f"{self.band_powers.get('theta_rel', 25.0):.2f} %"),
                ("Alpha Band Relative Power", f"{self.band_powers.get('alpha_rel', 25.0):.2f} %"),
                ("Beta Band Relative Power", f"{self.band_powers.get('beta_rel', 25.0):.2f} %"),
                ("DSP Calculation Latency", f"{self.metrics.get('calc_latency_ms', 1.4):.2f} ms")
            ]

            self.table_widget.setRowCount(len(feature_rows))
            for r, (k, v) in enumerate(feature_rows):
                item_k = QTableWidgetItem(k)
                item_v = QTableWidgetItem(v)
                item_k.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                item_v.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                item_v.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(r, 0, item_k)
                self.table_widget.setItem(r, 1, item_v)
