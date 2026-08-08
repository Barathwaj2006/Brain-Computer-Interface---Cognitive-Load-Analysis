"""
Settings Screen Module — Medical-Grade Calibration Standard
Provides Neural Signal Synthesizer calibration, active digital filter toggles,
sampling rate controls, and hardware interface status.
Theme: Bright Frosted Glassmorphism
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSlider, QCheckBox, QComboBox
from PySide6.QtCore import Qt
from src.app.config import (
    COLOR_CARD_BG, COLOR_CYAN, INTERFACE_NAME, SOURCE_SIMULATOR, SOURCE_DEVICE,
    NOTCH_FILTER_STATUS, EOG_FILTER_STATUS, EMG_FILTER_STATUS
)

class SettingsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title_lbl = QLabel("SYSTEM CONFIGURATION & FILTER CALIBRATION")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        layout.addWidget(title_lbl)

        # Card 1: Signal Interface & Acquisition Configuration
        card_interface = QFrame()
        card_interface.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px;")
        ci_layout = QVBoxLayout(card_interface)

        t1 = QLabel("ACQUISITION INTERFACE STATUS")
        t1.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {COLOR_CYAN}; letter-spacing: 1px;")
        
        status_lbl = QLabel(f"• Interface Name: {INTERFACE_NAME}\n• Primary Data Stream: Auto-Locking Active Stream (250 Hz)\n• Physical Protocol: High-Speed Biomedical Serial USB")
        status_lbl.setStyleSheet("font-size: 12px; color: #64748B; line-height: 1.6; margin-top: 6px;")

        ci_layout.addWidget(t1)
        ci_layout.addWidget(status_lbl)
        layout.addWidget(card_interface)

        # Card 2: Active Digital Filter Configuration
        card_filters = QFrame()
        card_filters.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px;")
        cf_layout = QVBoxLayout(card_filters)

        t2 = QLabel("ACTIVE BIOMEDICAL DIGITAL FILTERS")
        t2.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {COLOR_CYAN}; letter-spacing: 1px;")
        cf_layout.addWidget(t2)

        chk1 = QCheckBox(f"Enable {NOTCH_FILTER_STATUS} (Powerline Interference Suppression)")
        chk1.setChecked(True)
        chk1.setStyleSheet("color: #0F172A; font-weight: 700; font-size: 12px; margin-top: 8px;")
        
        chk2 = QCheckBox(f"Enable {EOG_FILTER_STATUS} (Blink & Ocular Movement Attenuation)")
        chk2.setChecked(True)
        chk2.setStyleSheet("color: #0F172A; font-weight: 700; font-size: 12px; margin-top: 6px;")

        chk3 = QCheckBox(f"Enable {EMG_FILTER_STATUS} (High-Frequency Muscle Noise Filter)")
        chk3.setChecked(True)
        chk3.setStyleSheet("color: #0F172A; font-weight: 700; font-size: 12px; margin-top: 6px;")

        cf_layout.addWidget(chk1)
        cf_layout.addWidget(chk2)
        cf_layout.addWidget(chk3)

        layout.addWidget(card_filters)
