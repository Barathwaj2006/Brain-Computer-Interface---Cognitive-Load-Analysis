"""
Signal Laboratory Screen Module
Allows judges and researchers to inspect every stage of the DSP pipeline:
Stage 1: Raw Signal -> Stage 2: Filtered Signal -> Stage 3: Welch PSD -> Stage 4: Band Decomposition -> Stage 5: Extracted Features
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QStackedWidget, QPushButton, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt
import pyqtgraph as pg

from src.app.config import COLOR_CYAN, COLOR_EMERALD, COLOR_PURPLE, COLOR_AMBER, COLOR_CARD_BG

class SignalLabScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Left Stage Navigation Menu
        nav_card = QFrame()
        nav_card.setFixedWidth(240)
        nav_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px;")
        n_layout = QVBoxLayout(nav_card)
        
        n_title = QLabel("DSP PIPELINE STAGES")
        n_title.setStyleSheet("font-size: 11px; font-weight: 900; color: #94A3B8; letter-spacing: 1px; margin-bottom: 8px;")
        n_layout.addWidget(n_title)

        self.stage_list = QListWidget()
        self.stage_list.setStyleSheet("""
            QListWidget { background: transparent; border: none; }
            QListWidget::item { padding: 12px; border-radius: 8px; color: #94A3B8; font-weight: 700; font-size: 12px; }
            QListWidget::item:selected { background: rgba(6,182,212,0.15); color: #06B6D4; }
        """)

        stages = [
            "1. Raw Signal",
            "2. Butterworth Filtered",
            "3. Welch PSD Spectrum",
            "4. Band Decomposition",
            "5. Feature Extraction"
        ]
        for s in stages:
            self.stage_list.addItem(QListWidgetItem(s))
        
        self.stage_list.setCurrentRow(0)
        self.stage_list.currentRowChanged.connect(self.switch_stage)
        n_layout.addWidget(self.stage_list)
        
        layout.addWidget(nav_card)

        # Right Stage Display Area
        display_card = QFrame()
        display_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px;")
        d_layout = QVBoxLayout(display_card)

        self.stage_title = QLabel("STAGE 1 — RAW EEG SIGNAL INPUT")
        self.stage_title.setStyleSheet("font-size: 14px; font-weight: 900; color: #06B6D4; letter-spacing: 1px;")
        d_layout.addWidget(self.stage_title)

        self.stage_desc = QLabel("Displays un-filtered composite waveform before bandpass filtering.")
        self.stage_desc.setStyleSheet("font-size: 11px; color: #94A3B8; margin-bottom: 12px;")
        d_layout.addWidget(self.stage_desc)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(None)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen(color=COLOR_CYAN, width=2))
        d_layout.addWidget(self.plot_widget)

        layout.addWidget(display_card)

    def switch_stage(self, index):
        descriptions = [
            ("STAGE 1 — RAW SIGNAL INPUT", "Un-filtered composite waveform directly from simulator or ESP32 device."),
            ("STAGE 2 — BUTTERWORTH BANDPASS (0.5 - 40 Hz)", "Filtered time-series signal with DC offset and high-frequency noise removed."),
            ("STAGE 3 — WELCH POWER SPECTRAL DENSITY", "FFT power spectrum distribution (0-40 Hz) using 5-second overlapping windows."),
            ("STAGE 4 — BAND POWER DECOMPOSITION", "Integrated relative power ratios across Delta, Theta, Alpha, and Beta frequency bands."),
            ("STAGE 5 — EXTRACTED FEATURE VECTOR", "Calculated Spectral Stress Index, TBR ratio, and feature vector ready for classification.")
        ]
        if 0 <= index < len(descriptions):
            self.stage_title.setText(descriptions[index][0])
            self.stage_desc.setText(descriptions[index][1])

    def update_lab_data(self, wave_data):
        if len(wave_data) > 0:
            self.plot_curve.setData(wave_data[-300:])
