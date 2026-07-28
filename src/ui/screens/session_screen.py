"""
Screen 5 — Live Session Control & Recording Screen
Controls for starting, pausing, stopping, and logging sessions into SQLite database.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout
from PySide6.QtCore import Qt, Signal
from src.app.config import COLORS
from src.visualization.custom_widgets import GlassCard, MetricCard

class SessionScreen(QWidget):
    start_session_signal = Signal()
    pause_session_signal = Signal()
    stop_session_signal  = Signal()
    reset_session_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("SESSION RECORDING & CONTROL CENTER")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        layout.addWidget(title)

        # Metrics Row
        grid = QGridLayout()
        grid.setSpacing(14)

        self.m_id = MetricCard("Session ID", "SESS-1001", "", "Unique Database Reference", COLORS['accent_cyan'])
        self.m_dur = MetricCard("Elapsed Duration", "00:00", "", "Recording Time", COLORS['accent_emerald'])
        self.m_samples = MetricCard("Samples Logged", "0", "", "250 Hz Sample Stream", COLORS['accent_purple'])
        self.m_class = MetricCard("Live Classification", "READY", "", "Real-time State Prediction", COLORS['accent_amber'])

        grid.addWidget(self.m_id, 0, 0)
        grid.addWidget(self.m_dur, 0, 1)
        grid.addWidget(self.m_samples, 0, 2)
        grid.addWidget(self.m_class, 0, 3)

        layout.addLayout(grid)

        # Controls Card
        ctrl_card = GlassCard()
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(24, 20, 24, 20)

        ctrl_title = QLabel("SESSION RECORDING CONTROLS")
        ctrl_title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {COLORS['text_muted']}; letter-spacing: 1px;")
        ctrl_layout.addWidget(ctrl_title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        self.btn_start = QPushButton("▶ START SESSION")
        self.btn_start.setProperty("class", "PrimaryBtn")
        self.btn_start.setStyleSheet(f"background: {COLORS['accent_emerald']}; font-size: 14px; padding: 12px 24px;")
        self.btn_start.clicked.connect(self.start_session_signal.emit)

        self.btn_pause = QPushButton("⏸ PAUSE")
        self.btn_pause.setProperty("class", "SecondaryBtn")
        self.btn_pause.setStyleSheet("font-size: 14px; padding: 12px 24px;")
        self.btn_pause.clicked.connect(self.pause_session_signal.emit)

        self.btn_stop = QPushButton("⏹ STOP & SAVE")
        self.btn_stop.setProperty("class", "DangerBtn")
        self.btn_stop.setStyleSheet("font-size: 14px; padding: 12px 24px;")
        self.btn_stop.clicked.connect(self.stop_session_signal.emit)

        self.btn_reset = QPushButton("🔄 RESET")
        self.btn_reset.setProperty("class", "SecondaryBtn")
        self.btn_reset.setStyleSheet("font-size: 14px; padding: 12px 24px;")
        self.btn_reset.clicked.connect(self.reset_session_signal.emit)

        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_pause)
        btn_row.addWidget(self.btn_stop)
        btn_row.addWidget(self.btn_reset)

        ctrl_layout.addLayout(btn_row)
        layout.addWidget(ctrl_card)
        layout.addStretch()

    def update_session_info(self, sess_id: str, duration_sec: float, sample_count: int, live_state: str, is_recording: bool):
        self.m_id.update_value(sess_id)
        mins = int(duration_sec) // 60
        secs = int(duration_sec) % 60
        self.m_dur.update_value(f"{mins:02d}:{secs:02d}")
        self.m_samples.update_value(f"{sample_count:,}")
        self.m_class.update_value(live_state)

        if is_recording:
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
        else:
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
