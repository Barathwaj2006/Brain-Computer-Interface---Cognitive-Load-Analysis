"""
Screen 1 — Splash / Start Screen
High-end visual splash screen with animated brain canvas, title branding, and progress initialization.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from src.app.config import APP_NAME, APP_SUBTITLE, COLORS
from src.visualization.animated_brain import AnimatedBrainCanvas

class SplashScreen(QWidget):
    start_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Animated Brain Graphic Canvas
        self.brain_canvas = AnimatedBrainCanvas(self)
        layout.addWidget(self.brain_canvas, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title Branding
        title = QLabel(APP_NAME)
        title.setStyleSheet(f"font-size: 38px; font-weight: 900; color: {COLORS['accent_cyan']}; letter-spacing: 4px;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(APP_SUBTITLE)
        subtitle.setStyleSheet(f"font-size: 14px; font-weight: 500; color: {COLORS['text_secondary']};")
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

        # Progress Initialization Bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedWidth(360)
        self.progress.setFixedHeight(8)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #151D2A;
                border-radius: 4px;
                border: 1px solid #1E293B;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent_cyan']};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.progress, alignment=Qt.AlignmentFlag.AlignCenter)

        self.status_lbl = QLabel("Initializing Signal Processing Engine...")
        self.status_lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']};")
        layout.addWidget(self.status_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # Enter System Button
        self.enter_btn = QPushButton("ENTER PLATFORM →")
        self.enter_btn.setFixedWidth(220)
        self.enter_btn.setFixedHeight(45)
        self.enter_btn.setProperty("class", "PrimaryBtn")
        self.enter_btn.setVisible(False)
        self.enter_btn.clicked.connect(self.start_requested.emit)
        layout.addWidget(self.enter_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Auto Progress Simulation
        self.load_val = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._step_loading)
        self.timer.start(25)

    def _step_loading(self):
        self.load_val += 3
        self.progress.setValue(self.load_val)
        if self.load_val >= 100:
            self.timer.stop()
            self.status_lbl.setText("SYSTEM READY — Synthetic EEG Cognitive Engine Online")
            self.enter_btn.setVisible(True)
