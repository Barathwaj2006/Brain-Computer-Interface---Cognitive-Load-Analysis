"""
Technical Status Bar Component
Bottom scientific status bar presenting live stream telemetry:
Signal Source, Sampling Rate, DSP Latency, Packet Counter, and Session State.
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from src.app.config import COLOR_CARD_BG, COLOR_BORDER, COLOR_CYAN, COLOR_EMERALD, COLOR_TEXT_MUTED

class TechnicalStatusBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CARD_BG};
                border-top: 1px solid {COLOR_BORDER};
            }}
            QLabel {{
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                color: {COLOR_TEXT_MUTED};
            }}
        """)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 2, 16, 2)
        layout.setSpacing(20)

        self.lbl_source = QLabel("Signal: SIMULATED (NeuroSim Signal Simulator)")
        self.lbl_rate = QLabel("Rate: 250 Hz")
        self.lbl_latency = QLabel("DSP Latency: 1.4 ms")
        self.lbl_packets = QLabel("Packets: 0")
        self.lbl_session = QLabel("Session: READY")

        layout.addWidget(self.lbl_source)
        layout.addWidget(self.lbl_rate)
        layout.addWidget(self.lbl_latency)
        layout.addWidget(self.lbl_packets)
        layout.addStretch()
        layout.addWidget(self.lbl_session)

    def update_status(self, source="SIMULATED", rate=250, latency_ms=1.4, packets=0, session="READY"):
        if "ESP32" in source:
            self.lbl_source.setText(f"Signal: LIVE DEVICE ({source})")
            self.lbl_source.setStyleSheet("color: #10B981; font-weight: bold;")
        else:
            self.lbl_source.setText("Signal: SIMULATED (NeuroSim Signal Simulator)")
            self.lbl_source.setStyleSheet("color: #0EA5E9; font-weight: bold;")

        self.lbl_rate.setText(f"Rate: {rate} Hz")
        self.lbl_latency.setText(f"DSP Latency: {latency_ms:.1f} ms")
        self.lbl_packets.setText(f"Packets: {packets:,}")
        self.lbl_session.setText(f"Session: {session.upper()}")
