"""
Screen 2 — Home Dashboard Screen
System status grid, acquisition mode toggles, and quick action launch pad.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from src.app.config import COLORS
from src.visualization.custom_widgets import GlassCard, StatusBadge, MetricCard

class HomeScreen(QWidget):
    start_session_requested = Signal()
    set_mode_requested = Signal(str)  # 'SIMULATION' or 'HARDWARE'
    nav_requested = Signal(str)       # Screen name

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header Title
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("SYSTEM STATUS DASHBOARD")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['text_primary']};")
        subtitle = QLabel("Overview of signal acquisition, connection state, and system readiness.")
        subtitle.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header_layout.addLayout(title_box)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Status Cards Grid
        grid = QGridLayout()
        grid.setSpacing(16)

        self.card_esp32 = MetricCard("ESP32 Hardware", "DISCONNECTED", "", "COM Port: Auto-Scan", COLORS['accent_rose'])
        self.card_mode = MetricCard("Acquisition Mode", "SIMULATION", "", "Interactive Waveform Generator", COLORS['accent_cyan'])
        self.card_srate = MetricCard("Sampling Rate", "250 Hz", "", "Target DSP Bandwidth", COLORS['accent_emerald'])
        self.card_session = MetricCard("Session State", "READY", "", "Database Storage Ready", COLORS['accent_purple'])
        self.card_signal = MetricCard("Signal Health", "ACTIVE", "", "5 sec Window Buffer", COLORS['accent_emerald'])

        grid.addWidget(self.card_esp32, 0, 0)
        grid.addWidget(self.card_mode, 0, 1)
        grid.addWidget(self.card_srate, 0, 2)
        grid.addWidget(self.card_session, 1, 0)
        grid.addWidget(self.card_signal, 1, 1)

        layout.addLayout(grid)

        # Mode Selection & Action Panel
        actions_card = GlassCard()
        act_layout = QVBoxLayout(actions_card)
        act_layout.setContentsMargins(20, 20, 20, 20)
        act_layout.setSpacing(16)

        act_title = QLabel("ACQUISITION MODE & CONTROL LAUNCHER")
        act_title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLORS['text_muted']}; letter-spacing: 1px;")
        act_layout.addWidget(act_title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.sim_mode_btn = QPushButton("⚡ SIMULATION MODE")
        self.sim_mode_btn.setProperty("class", "PrimaryBtn")
        self.sim_mode_btn.clicked.connect(lambda: self.set_mode_requested.emit('SIMULATION'))

        self.hw_mode_btn = QPushButton("🔌 HARDWARE MODE (ESP32)")
        self.hw_mode_btn.setProperty("class", "SecondaryBtn")
        self.hw_mode_btn.clicked.connect(lambda: self.set_mode_requested.emit('HARDWARE'))

        self.start_btn = QPushButton("▶ START LIVE SESSION")
        self.start_btn.setProperty("class", "PrimaryBtn")
        self.start_btn.setStyleSheet(f"background: {COLORS['accent_emerald']};")
        self.start_btn.clicked.connect(self.start_session_requested.emit)

        self.history_btn = QPushButton("📁 VIEW HISTORY")
        self.history_btn.setProperty("class", "SecondaryBtn")
        self.history_btn.clicked.connect(lambda: self.nav_requested.emit('history'))

        self.settings_btn = QPushButton("⚙ SETTINGS")
        self.settings_btn.setProperty("class", "SecondaryBtn")
        self.settings_btn.clicked.connect(lambda: self.nav_requested.emit('settings'))

        btn_row.addWidget(self.sim_mode_btn)
        btn_row.addWidget(self.hw_mode_btn)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.history_btn)
        btn_row.addWidget(self.settings_btn)

        act_layout.addLayout(btn_row)
        layout.addWidget(actions_card)
        layout.addStretch()

    def update_system_status(self, is_hw: bool, esp_connected: bool, is_recording: bool):
        mode_str = "HARDWARE" if is_hw else "SIMULATION"
        self.card_mode.update_value(mode_str, "", "Serial Data Stream" if is_hw else "Interactive Generator")
        
        esp_str = "CONNECTED" if esp_connected else "DISCONNECTED"
        esp_color = COLORS['accent_emerald'] if esp_connected else COLORS['accent_rose']
        self.card_esp32.update_value(esp_str, "", "Serial Port Active" if esp_connected else "Plug USB Serial Cable", esp_color)

        sess_str = "RECORDING..." if is_recording else "READY"
        sess_color = COLORS['accent_amber'] if is_recording else COLORS['accent_purple']
        self.card_session.update_value(sess_str, "", "Logging to SQLite" if is_recording else "Ready for Session", sess_color)
