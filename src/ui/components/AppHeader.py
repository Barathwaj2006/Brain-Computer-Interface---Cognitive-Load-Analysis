"""
Application Header Component
Top branded navigation bar featuring logo, application title, permanent signal-source selector,
sampling rate indicator, and live connection status.
"""

import os
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from src.app.config import APP_NAME, APP_TAGLINE, COLOR_CARD_BG, COLOR_BORDER, COLOR_CYAN, COLOR_EMERALD, COLOR_AMBER

class AppHeader(QFrame):
    source_changed = Signal(str)  # 'SIMULATOR' or 'ESP32'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CARD_BG};
                border-bottom: 1px solid {COLOR_BORDER};
            }}
        """)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(16)

        # Brand Container (Left)
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(12)

        logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "logo_icon.png")
        if os.path.exists(logo_path):
            img_lbl = QLabel()
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                img_lbl.setPixmap(pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                brand_layout.addWidget(img_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        
        t_lbl = QLabel(APP_NAME)
        t_lbl.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {COLOR_CYAN}; letter-spacing: 2px;")
        
        sub_lbl = QLabel(APP_TAGLINE)
        sub_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #9CA3AF; letter-spacing: 0.5px;")

        title_box.addWidget(t_lbl)
        title_box.addWidget(sub_lbl)
        brand_layout.addLayout(title_box)

        layout.addLayout(brand_layout)
        layout.addStretch()

        # Telemetry Controls (Right)
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(12)

        # Permanent Signal Source Selector
        source_box = QHBoxLayout()
        source_lbl = QLabel("SIGNAL SOURCE:")
        source_lbl.setStyleSheet("font-size: 10px; font-weight: 800; color: #9CA3AF; letter-spacing: 1px;")
        
        self.combo_source = QComboBox()
        self.combo_source.addItems(["Signal Simulator", "ESP32 Controller"])
        self.combo_source.setStyleSheet("""
            QComboBox {
                background: #1F2937;
                color: #F9FAFB;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 5px 12px;
                font-weight: 700;
                font-size: 11px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #111827;
                color: #F9FAFB;
                selection-background-color: #0EA5E9;
            }
        """)
        self.combo_source.currentIndexChanged.connect(self.on_source_changed)

        source_box.addWidget(source_lbl)
        source_box.addWidget(self.combo_source)
        ctrl_layout.addLayout(source_box)

        # Sampling Rate Badge
        self.badge_fs = QLabel("250 Hz")
        self.badge_fs.setStyleSheet("background: rgba(14, 165, 233, 0.12); color: #0EA5E9; border: 1px solid rgba(14, 165, 233, 0.3); padding: 5px 10px; border-radius: 6px; font-weight: 800; font-size: 10px;")
        ctrl_layout.addWidget(self.badge_fs)

        # Live Signal Source Indicator Badge
        self.badge_source = QLabel("● SIMULATED EEG")
        self.badge_source.setStyleSheet("background: rgba(16, 185, 129, 0.12); color: #10B981; border: 1px solid #10B981; padding: 5px 12px; border-radius: 6px; font-weight: 800; font-size: 10px;")
        ctrl_layout.addWidget(self.badge_source)

        # Session Status Badge
        self.badge_session = QLabel("SESSION: READY")
        self.badge_session.setStyleSheet("background: #1F2937; color: #9CA3AF; border: 1px solid #374151; padding: 5px 10px; border-radius: 6px; font-weight: 700; font-size: 10px;")
        ctrl_layout.addWidget(self.badge_session)

        layout.addLayout(ctrl_layout)

    def on_source_changed(self, index):
        if index == 0:
            self.badge_source.setText("● SIMULATED EEG")
            self.badge_source.setStyleSheet("background: rgba(16, 185, 129, 0.12); color: #10B981; border: 1px solid #10B981; padding: 5px 12px; border-radius: 6px; font-weight: 800; font-size: 10px;")
            self.source_changed.emit("SIMULATOR")
        else:
            self.badge_source.setText("● ESP32 INPUT (COM7)")
            self.badge_source.setStyleSheet("background: rgba(245, 158, 11, 0.12); color: #F59E0B; border: 1px solid #F59E0B; padding: 5px 12px; border-radius: 6px; font-weight: 800; font-size: 10px;")
            self.source_changed.emit("ESP32")

    def set_hardware_status(self, is_connected, port_name="COM7"):
        if is_connected:
            self.badge_source.setText(f"● ESP32 CONNECTED ({port_name})")
            self.badge_source.setStyleSheet("background: rgba(16, 185, 129, 0.12); color: #10B981; border: 1px solid #10B981; padding: 5px 12px; border-radius: 6px; font-weight: 800; font-size: 10px;")
        else:
            self.badge_source.setText("● ESP32 DISCONNECTED")
            self.badge_source.setStyleSheet("background: rgba(239, 68, 68, 0.12); color: #EF4444; border: 1px solid #EF4444; padding: 5px 12px; border-radius: 6px; font-weight: 800; font-size: 10px;")

    def set_session_status(self, status_text, is_active=False):
        self.badge_session.setText(f"SESSION: {status_text.upper()}")
        if is_active:
            self.badge_session.setStyleSheet("background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid #EF4444; padding: 5px 10px; border-radius: 6px; font-weight: 800; font-size: 10px;")
        else:
            self.badge_session.setStyleSheet("background: #1F2937; color: #9CA3AF; border: 1px solid #374151; padding: 5px 10px; border-radius: 6px; font-weight: 700; font-size: 10px;")
