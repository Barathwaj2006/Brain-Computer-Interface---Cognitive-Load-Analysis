"""
Main Window Controller Module
Manages application architecture, sidebar navigation, screen switching,
live DSP thread data dispatch, and global telemetry.
"""

from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem, QStackedWidget, QLabel, QFrame, QPushButton
from PySide6.QtCore import Qt, QTimer
import numpy as np

from src.app.config import APP_TITLE, APP_LOGO_TEXT, STATUS_BADGE, COLOR_BACKGROUND, COLOR_SIDEBAR_BG, COLOR_CYAN
from src.simulation.eeg_generator import SyntheticEEGGenerator
from src.processing.psd import PSDAnalyzer
from src.classification.rule_classifier import RuleBasedClassifier

# Import All Screens
from src.ui.screens.overview_screen import OverviewScreen
from src.ui.screens.live_monitor_screen import LiveMonitorScreen
from src.ui.screens.band_analysis_screen import BandAnalysisScreen
from src.ui.screens.session_screen import SessionScreen
from src.ui.screens.summary_screen import SummaryScreen
from src.ui.screens.report_screen import ReportScreen
from src.ui.screens.history_screen import HistoryScreen
from src.ui.screens.settings_screen import SettingsScreen
from src.ui.screens.signal_lab_screen import SignalLabScreen
from src.ui.screens.validation_screen import ValidationScreen
from src.ui.screens.architecture_screen import ArchitectureScreen
from src.ui.screens.experiment_screen import ExperimentScreen
from src.ui.screens.compare_screen import CompareScreen
from src.ui.screens.presentation_mode import PresentationModeScreen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1340, 840)

        self.generator = SyntheticEEGGenerator()
        self.psd_analyzer = PSDAnalyzer()
        self.classifier = RuleBasedClassifier()

        self.signal_buffer = []
        self.init_ui()
        self.init_dsp_timer()

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left Sidebar Navigation
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet(f"background: {COLOR_SIDEBAR_BG}; border-right: 1px solid rgba(255,255,255,0.08);")
        sb_layout = QVBoxLayout(self.sidebar)
        sb_layout.setContentsMargins(16, 20, 16, 20)
        sb_layout.setSpacing(12)

        # Brand Header
        logo_lbl = QLabel(APP_LOGO_TEXT)
        logo_lbl.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {COLOR_CYAN}; letter-spacing: 1.5px;")
        
        tag_lbl = QLabel("Neural Intelligence Platform")
        tag_lbl.setStyleSheet("font-size: 9px; font-weight: 700; color: #94A3B8; letter-spacing: 1px;")

        sb_layout.addWidget(logo_lbl)
        sb_layout.addWidget(tag_lbl)

        badge_lbl = QLabel(STATUS_BADGE)
        badge_lbl.setStyleSheet("background: rgba(6,182,212,0.12); color: #06B6D4; border: 1px solid rgba(6,182,212,0.3); padding: 4px 10px; border-radius: 10px; font-size: 9px; font-weight: 800; margin-top: 6px;")
        sb_layout.addWidget(badge_lbl)

        # Nav List
        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet("""
            QListWidget { background: transparent; border: none; }
            QListWidget::item { padding: 10px 14px; border-radius: 8px; color: #94A3B8; font-weight: 700; font-size: 12px; margin-bottom: 2px; }
            QListWidget::item:selected { background: linear-gradient(90deg, rgba(6,182,212,0.15), transparent); color: #06B6D4; }
        """)

        nav_items = [
            "01 Overview",
            "02 Live Monitor",
            "03 Signal Lab",
            "04 Band Analysis",
            "05 Experiments",
            "06 Session Control",
            "07 Session Compare",
            "08 Reports & AI",
            "09 Validation Center",
            "10 Architecture",
            "11 History Archive",
            "12 Settings"
        ]

        for item in nav_items:
            self.nav_list.addItem(QListWidgetItem(item))

        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self.switch_screen)
        sb_layout.addWidget(self.nav_list)

        # Expo Demo Button
        btn_expo = QPushButton("⚡ PRESENTATION MODE")
        btn_expo.setStyleSheet("background: linear-gradient(135deg, #8B5CF6, #6D28D9); color: white; font-weight: 800; font-size: 11px; padding: 12px; border-radius: 8px; border: none;")
        btn_expo.setCursor(Qt.PointingHandCursor)
        btn_expo.clicked.connect(self.open_presentation_mode)
        sb_layout.addWidget(btn_expo)

        main_layout.addWidget(self.sidebar)

        # Right Stacked Screens
        self.stacked_widget = QStackedWidget()
        
        self.screen_overview = OverviewScreen()
        self.screen_overview.start_session_requested.connect(lambda: self.nav_list.setCurrentRow(5))
        
        self.screen_monitor = LiveMonitorScreen()
        self.screen_signal_lab = SignalLabScreen()
        self.screen_band = BandAnalysisScreen()
        self.screen_experiment = ExperimentScreen()
        self.screen_session = SessionScreen()
        self.screen_compare = CompareScreen()
        self.screen_report = ReportScreen()
        self.screen_validation = ValidationScreen()
        self.screen_architecture = ArchitectureScreen()
        self.screen_history = HistoryScreen()
        self.screen_settings = SettingsScreen()
        self.screen_presentation = PresentationModeScreen()
        self.screen_presentation.exit_presentation.connect(self.close_presentation_mode)

        self.stacked_widget.addWidget(self.screen_overview)       # 0
        self.stacked_widget.addWidget(self.screen_monitor)        # 1
        self.stacked_widget.addWidget(self.screen_signal_lab)     # 2
        self.stacked_widget.addWidget(self.screen_band)           # 3
        self.stacked_widget.addWidget(self.screen_experiment)     # 4
        self.stacked_widget.addWidget(self.screen_session)        # 5
        self.stacked_widget.addWidget(self.screen_compare)        # 6
        self.stacked_widget.addWidget(self.screen_report)         # 7
        self.stacked_widget.addWidget(self.screen_validation)     # 8
        self.stacked_widget.addWidget(self.screen_architecture)   # 9
        self.stacked_widget.addWidget(self.screen_history)        # 10
        self.stacked_widget.addWidget(self.screen_settings)       # 11
        self.stacked_widget.addWidget(self.screen_presentation)   # 12

        main_layout.addWidget(self.stacked_widget)

    def switch_screen(self, row):
        if 0 <= row < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(row)

    def open_presentation_mode(self):
        self.sidebar.hide()
        self.stacked_widget.setCurrentIndex(12)
        self.showFullScreen()

    def close_presentation_mode(self):
        self.showNormal()
        self.sidebar.show()
        self.stacked_widget.setCurrentIndex(0)

    def init_dsp_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_dsp_frame)
        self.timer.start(40)  # 25 FPS update rate

    def process_dsp_frame(self):
        # Generate new synthetic chunk
        chunk, _ = self.generator.generate_chunk(num_samples=10)
        self.signal_buffer.extend(chunk)
        if len(self.signal_buffer) > 1250:
            self.signal_buffer = self.signal_buffer[-1250:]

        signal_arr = np.array(self.signal_buffer)
        freqs, psd = self.psd_analyzer.compute_psd(signal_arr)
        band_powers = self.psd_analyzer.extract_band_powers(freqs, psd)
        metrics = self.psd_analyzer.compute_metrics(band_powers, freqs, psd)
        
        load_class, conf = self.classifier.classify(band_powers, metrics['stress_index'])
        metrics['load_class'] = load_class

        # Update active screens
        self.screen_overview.update_overview(signal_arr, band_powers, metrics)
        self.screen_monitor.update_monitor(signal_arr, freqs, psd)
        self.screen_signal_lab.update_lab_data(signal_arr)
        self.screen_presentation.update_presentation(signal_arr, metrics)
