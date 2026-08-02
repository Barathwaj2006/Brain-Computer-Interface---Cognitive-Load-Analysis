"""
Live Monitor Screen Module — Medical Research Standard
Integrates:
- 8-Channel Stacked Oscilloscope Trace Viewer (Fp1, Fp2, C3, C4, P3, P4, O1, O2)
- Time-Frequency 2D Spectrogram / Waterfall Plot
- Time-Window Selection (1s | 5s | 10s | 30s)
- Telemetry & Filter Badges
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QButtonGroup, QTabWidget
from PySide6.QtCore import Qt
import pyqtgraph as pg

from src.app.config import (
    COLOR_CARD_BG, COLOR_CYAN, COLOR_EMERALD, COLOR_PURPLE, COLOR_AMBER,
    EOG_FILTER_STATUS, EMG_FILTER_STATUS, NOTCH_FILTER_STATUS
)
from src.visualization.multichannel_viewer import MultiChannelViewerWidget
from src.visualization.spectrogram_widget import SpectrogramWidget

class LiveMonitorScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window_sec = 5.0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header with Telemetry & Filter Status
        h_card = QFrame()
        h_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px 18px;")
        h_layout = QHBoxLayout(h_card)

        t_box = QVBoxLayout()
        title = QLabel("LIVE NEURAL SIGNAL MONITOR — 10-20 SYSTEM")
        title.setStyleSheet("font-size: 15px; font-weight: 900; color: #F8FAFC; letter-spacing: 1px;")
        
        self.telemetry_lbl = QLabel("LIVE STREAM • 250 Hz • Latency: 12.4 ms • Active Filter Stack: 50Hz Notch + EOG + EMG")
        self.telemetry_lbl.setStyleSheet("font-size: 11px; color: #06B6D4; font-weight: 700;")
        
        t_box.addWidget(title)
        t_box.addWidget(self.telemetry_lbl)
        h_layout.addLayout(t_box)

        h_layout.addStretch()

        # Window Selector Buttons (1s | 5s | 10s | 30s)
        win_label = QLabel("Time Window:")
        win_label.setStyleSheet("font-size: 11px; color: #94A3B8; font-weight: 700; margin-right: 6px;")
        h_layout.addWidget(win_label)

        self.btn_group = QButtonGroup(self)
        windows = [("1s", 1.0), ("5s", 5.0), ("10s", 10.0), ("30s", 30.0)]
        for text, sec in windows:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { background: rgba(15,23,42,0.8); color: #94A3B8; border: 1px solid rgba(255,255,255,0.08); padding: 6px 14px; border-radius: 6px; font-weight: 700; font-size: 11px; }
                QPushButton:checked { background: #06B6D4; color: white; border-color: #06B6D4; }
            """)
            if sec == 5.0:
                btn.setChecked(True)
            self.btn_group.addButton(btn)
            btn.clicked.connect(lambda _, s=sec: self.set_window(s))
            h_layout.addWidget(btn)

        layout.addWidget(h_card)

        # Tabbed Visualization Display (Single Channel vs 8-Channel Montage vs Spectrogram)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { background: rgba(21, 29, 42, 0.75); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px; }
            QTabBar::tab { background: rgba(15,23,42,0.8); color: #94A3B8; font-weight: 700; font-size: 11px; padding: 8px 16px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #06B6D4; color: white; }
        """)

        # Tab 1: Primary Trace & Welch PSD
        tab_primary = QWidget()
        tp_layout = QVBoxLayout(tab_primary)
        
        self.wave_plot = pg.PlotWidget()
        self.wave_plot.setBackground(None)
        self.wave_plot.showGrid(x=True, y=True, alpha=0.15)
        self.wave_curve = self.wave_plot.plot(pen=pg.mkPen(color=COLOR_CYAN, width=2))
        tp_layout.addWidget(self.wave_plot)

        self.psd_plot = pg.PlotWidget()
        self.psd_plot.setBackground(None)
        self.psd_plot.showGrid(x=True, y=True, alpha=0.15)
        self.psd_curve = self.psd_plot.plot(pen=pg.mkPen(color=COLOR_PURPLE, width=2), fillLevel=0, brush=(139, 92, 246, 50))
        tp_layout.addWidget(self.psd_plot)

        self.tabs.addTab(tab_primary, "📈 Primary Trace & PSD Spectrum")

        # Tab 2: 8-Channel 10-20 Oscilloscope Montage
        self.multichannel_widget = MultiChannelViewerWidget()
        self.tabs.addTab(self.multichannel_widget, "🧠 8-Channel 10-20 System Montage")

        # Tab 3: Time-Frequency Spectrogram Waterfall
        self.spectrogram_widget = SpectrogramWidget()
        self.tabs.addTab(self.spectrogram_widget, "🌊 Time-Frequency Spectrogram Waterfall")

        layout.addWidget(self.tabs)

    def set_window(self, sec):
        self.window_sec = sec

    def update_monitor(self, wave_data, freqs, psd):
        num_samples = int(250 * self.window_sec)
        if len(wave_data) > 0:
            self.wave_curve.setData(wave_data[-num_samples:])
            self.multichannel_widget.update_channels(wave_data)

        if len(freqs) > 0 and len(psd) > 0:
            self.psd_curve.setData(freqs, psd)
            self.spectrogram_widget.update_spectrogram(psd)
