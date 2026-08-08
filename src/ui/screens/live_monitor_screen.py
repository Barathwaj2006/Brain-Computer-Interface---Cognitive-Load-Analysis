"""
Live Monitor Screen Module
Real-time neural signal visualization, multi-channel 10-20 montage,
Welch PSD frequency spectrum, and view window scaling (1s, 5s, 10s, 30s).
Theme: Bright Frosted Glassmorphism
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QTabWidget, QButtonGroup
from PySide6.QtCore import Qt
import pyqtgraph as pg

from src.app.config import COLOR_CARD_BG, COLOR_CYAN, COLOR_EMERALD, COLOR_PURPLE, COLOR_AMBER
from src.visualization.multichannel_viewer import MultiChannelViewerWidget
from src.visualization.spectrogram_view import SpectrogramWidget

class LiveMonitorScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window_sec = 5.0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header & Time Window Selection Bar
        h_card = QFrame()
        h_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px;")
        h_layout = QHBoxLayout(h_card)

        t_box = QVBoxLayout()
        title = QLabel("LIVE MONITOR & SPECTRUM OSCILLOSCOPE")
        title.setStyleSheet("font-size: 15px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        
        self.telemetry_lbl = QLabel("LIVE STREAM • 250 Hz • Latency: 1.4 ms • Active Filter Stack: 50Hz Notch + EOG + EMG")
        self.telemetry_lbl.setStyleSheet("font-size: 11px; color: #0284C7; font-weight: 700;")
        
        t_box.addWidget(title)
        t_box.addWidget(self.telemetry_lbl)
        h_layout.addLayout(t_box)

        h_layout.addStretch()

        # Window Selector Buttons (1s | 5s | 10s | 30s)
        win_label = QLabel("Time Window:")
        win_label.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 700; margin-right: 6px;")
        h_layout.addWidget(win_label)

        self.btn_group = QButtonGroup(self)
        windows = [("1s", 1.0), ("5s", 5.0), ("10s", 10.0), ("30s", 30.0)]
        for text, sec in windows:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; font-weight: 700; font-size: 11px; padding: 5px 12px; border-radius: 6px; }
                QPushButton:checked { background: #0284C7; color: white; border: none; }
            """)
            if sec == 5.0:
                btn.setChecked(True)
            btn.clicked.connect(lambda _, s=sec: self.set_window_sec(s))
            self.btn_group.addButton(btn)
            h_layout.addWidget(btn)

        layout.addWidget(h_card)

        # Tab Widget Container
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E2E8F0; border-radius: 12px; background: #FFFFFF; }
            QTabBar::tab { background: #F1F5F9; color: #64748B; font-weight: 800; font-size: 12px; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 4px; }
            QTabBar::tab:selected { background: #0284C7; color: #FFFFFF; }
        """)

        # Tab 1: Primary Trace & Welch PSD
        t1 = QWidget()
        t1_layout = QHBoxLayout(t1)

        self.trace_plot = pg.PlotWidget(title="PRIMARY WAVEFORM TRACE (Fp1)")
        self.trace_plot.setBackground('#FFFFFF')
        self.trace_plot.showGrid(x=True, y=True, alpha=0.15)
        self.trace_plot.setYRange(-80, 80, padding=0)  # Stabilize Y-axis range
        self.trace_curve = self.trace_plot.plot(pen=pg.mkPen(color='#0284C7', width=2))

        self.psd_plot = pg.PlotWidget(title="WELCH POWER SPECTRAL DENSITY (0-40 Hz)")
        self.psd_plot.setBackground('#FFFFFF')
        self.psd_plot.showGrid(x=True, y=True, alpha=0.15)
        self.psd_plot.setXRange(0, 40, padding=0)
        self.psd_plot.setYRange(0, 100, padding=0)   # Stabilize PSD Y-axis range
        self.psd_curve = self.psd_plot.plot(pen=pg.mkPen(color='#7C3AED', width=2))

        t1_layout.addWidget(self.trace_plot, stretch=1)
        t1_layout.addWidget(self.psd_plot, stretch=1)
        self.tabs.addTab(t1, "Primary Trace & PSD")

        # Tab 2: 8-Channel 10-20 Oscilloscope View
        self.multichannel_viewer = MultiChannelViewerWidget()
        self.tabs.addTab(self.multichannel_viewer, "8-Channel 10-20 System Montage")

        # Tab 3: Time-Frequency Spectrogram Waterfall
        self.spectrogram_widget = SpectrogramWidget()
        self.tabs.addTab(self.spectrogram_widget, "Time-Frequency Spectrogram Waterfall")

        layout.addWidget(self.tabs)

    def set_window_sec(self, sec):
        self.window_sec = sec

    def update_monitor(self, signal_arr, freqs, psd):
        if len(signal_arr) > 0:
            num_samples = int(self.window_sec * 250)
            disp_arr = signal_arr[-num_samples:] if len(signal_arr) >= num_samples else signal_arr
            self.trace_curve.setData(disp_arr)
            self.multichannel_viewer.update_channels(disp_arr)
            self.spectrogram_widget.update_spectrogram(disp_arr)

        if len(freqs) > 0 and len(psd) > 0:
            idx = freqs <= 40.0
            self.psd_curve.setData(freqs[idx], psd[idx])
