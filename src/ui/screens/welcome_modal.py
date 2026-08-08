"""
First-Run Welcome Modal Component
Displays interactive onboarding on first application launch explaining research workflows
and prompting initial signal source selection.
"""

import os
import json
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
from PySide6.QtCore import Qt, Signal
from src.app.config import APP_NAME, COLOR_CARD_BG, COLOR_BORDER, COLOR_CYAN, COLOR_EMERALD, COLOR_AMBER

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config_settings.json")

def is_first_run() -> bool:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                return not data.get('first_run_complete', False)
        except Exception:
            return True
    return True

def mark_first_run_complete():
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({'first_run_complete': True}, f)
    except Exception:
        pass

class WelcomeModal(QDialog):
    source_selected = Signal(str)  # 'SIMULATOR' or 'ESP32'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to NeuroSim")
        self.setFixedSize(650, 480)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #0B0F19;
                color: #F9FAFB;
            }}
            QFrame.Card {{
                background-color: {COLOR_CARD_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 10px;
                padding: 16px;
            }}
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Title
        h_box = QVBoxLayout()
        t_lbl = QLabel(f"Welcome to {APP_NAME}")
        t_lbl.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {COLOR_CYAN}; letter-spacing: 1px;")
        
        sub_lbl = QLabel("Explore EEG signal processing through a controlled synthetic research environment.")
        sub_lbl.setStyleSheet("font-size: 12px; color: #9CA3AF;")

        h_box.addWidget(t_lbl)
        h_box.addWidget(sub_lbl)
        layout.addLayout(h_box)

        # 4-Step Research Workflow Cards Grid
        grid_card = QFrame()
        grid_card.setProperty("class", "Card")
        grid = QGridLayout(grid_card)
        grid.setSpacing(12)

        self._add_step(grid, 0, 0, "1. Signal Generation", "Synthesize 8-channel EEG waveforms or stream live from ESP32 hardware.")
        self._add_step(grid, 0, 1, "2. Signal Processing", "Apply Welch PSD spectral estimation and band integration (Delta-Beta).")
        self._add_step(grid, 1, 0, "3. Cognitive Analytics", "Compare Rule-Based Heuristic Margins against ML Random Forest Probabilities.")
        self._add_step(grid, 1, 1, "4. Session Reporting", "Generate research PDF reports with automated AI narrative interpretation.")

        layout.addWidget(grid_card)

        # Choice Section
        choice_lbl = QLabel("CHOOSE INITIAL SIGNAL SOURCE:")
        choice_lbl.setStyleSheet("font-size: 11px; font-weight: 800; color: #9CA3AF; letter-spacing: 1px;")
        layout.addWidget(choice_lbl)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(14)

        btn_sim = QPushButton("⚡ SIGNAL SIMULATOR (RECOMMENDED)")
        btn_sim.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0EA5E9, stop:1 #0284C7);
                color: white;
                font-weight: 800;
                font-size: 12px;
                padding: 12px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{ background: #0284C7; }}
        """)
        btn_sim.clicked.connect(self.select_simulator)

        btn_esp = QPushButton("🎛️ ESP32 CONTROLLER")
        btn_esp.setStyleSheet(f"""
            QPushButton {{
                background: #1F2937;
                color: #F9FAFB;
                font-weight: 800;
                font-size: 12px;
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #374151;
            }}
            QPushButton:hover {{ background: #374151; }}
        """)
        btn_esp.clicked.connect(self.select_esp32)

        btn_layout.addWidget(btn_sim, stretch=1)
        btn_layout.addWidget(btn_esp, stretch=1)
        layout.addLayout(btn_layout)

        # Footer Skip Button
        f_layout = QHBoxLayout()
        btn_skip = QPushButton("Skip Introduction")
        btn_skip.setStyleSheet("background: transparent; color: #6B7280; font-size: 11px; border: none;")
        btn_skip.setCursor(Qt.PointingHandCursor)
        btn_skip.clicked.connect(self.accept_modal)

        f_layout.addStretch()
        f_layout.addWidget(btn_skip)
        layout.addLayout(f_layout)

    def _add_step(self, grid, row, col, title, desc):
        card = QFrame()
        card.setStyleSheet("background: #1F2937; border-radius: 8px; padding: 12px;")
        l = QVBoxLayout(card)
        l.setSpacing(4)

        t = QLabel(title)
        t.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {COLOR_CYAN};")
        d = QLabel(desc)
        d.setStyleSheet("font-size: 10px; color: #9CA3AF;")
        d.setWordWrap(True)

        l.addWidget(t)
        l.addWidget(d)
        grid.addWidget(card, row, col)

    def select_simulator(self):
        mark_first_run_complete()
        self.source_selected.emit("SIMULATOR")
        self.accept()

    def select_esp32(self):
        mark_first_run_complete()
        self.source_selected.emit("ESP32")
        self.accept()

    def accept_modal(self):
        mark_first_run_complete()
        self.accept()
