"""
Main Window Controller Module
Manages application architecture, sidebar navigation, screen switching,
live DSP thread data dispatch, and global telemetry.
Theme: Bright Frosted Glassmorphism
"""

import os
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem, QStackedWidget, QLabel, QFrame, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
import numpy as np

from src.app.config import APP_TITLE, APP_LOGO_TEXT, STATUS_BADGE, COLOR_BACKGROUND, COLOR_SIDEBAR_BG, COLOR_CYAN
from src.simulation.eeg_generator import SyntheticEEGGenerator
from src.processing.psd import PSDAnalyzer
from src.classification.rule_classifier import RuleBasedClassifier
from src.classification.ml_classifier import MLClassifier

# Import All Screens
from src.ui.screens.overview_screen import OverviewScreen
from src.ui.screens.live_monitor_screen import LiveMonitorScreen
from src.ui.screens.band_analysis_screen import BandAnalysisScreen
from src.ui.screens.session_screen import SessionScreen
from src.ui.screens.report_screen import ReportScreen
from src.ui.screens.history_screen import HistoryScreen
from src.ui.screens.settings_screen import SettingsScreen
from src.ui.screens.signal_lab_screen import SignalLabScreen
from src.ui.screens.validation_screen import ValidationScreen
from src.ui.screens.architecture_screen import ArchitectureScreen
from src.ui.screens.experiment_screen import ExperimentScreen
from src.ui.screens.compare_screen import CompareScreen
from src.ui.screens.presentation_mode import PresentationModeScreen
from src.ui.screens.hardware_screen import HardwareScreen
from src.ui.screens.results_screen import ResultsScreen
from src.acquisition.serial_reader import HardwareSerialThread
from src.acquisition.device_scanner import WifiStreamThread
from src.acquisition.pokidex_client import PokidexDualStreamManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1360, 860)

        self.generator = SyntheticEEGGenerator()
        self.psd_analyzer = PSDAnalyzer()
        self.rule_classifier = RuleBasedClassifier()
        self.ml_classifier = MLClassifier()

        self.hw_serial_thread = None
        self.hw_wifi_thread = None
        self.pokidex_manager = PokidexDualStreamManager()
        self.active_hardware_source = "IDLE"

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

        # Left Sidebar Navigation — Bright Glassy White
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet("background: #FFFFFF; border-right: 1px solid #E2E8F0;")
        sb_layout = QVBoxLayout(self.sidebar)
        sb_layout.setContentsMargins(16, 16, 16, 16)
        sb_layout.setSpacing(8)

        # Logo Graphic Display
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.jpg")
        if os.path.exists(logo_path):
            img_lbl = QLabel()
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                img_lbl.setPixmap(pixmap.scaled(220, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                img_lbl.setAlignment(Qt.AlignCenter)
                img_lbl.setStyleSheet("border-radius: 10px; margin-bottom: 4px;")
                sb_layout.addWidget(img_lbl)

        # Brand Header Text
        logo_lbl = QLabel(APP_LOGO_TEXT)
        logo_lbl.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {COLOR_CYAN}; letter-spacing: 1.5px;")
        
        tag_lbl = QLabel("Neural Intelligence Platform")
        tag_lbl.setStyleSheet("font-size: 9px; font-weight: 700; color: #475569; letter-spacing: 1px;")

        sb_layout.addWidget(logo_lbl)
        sb_layout.addWidget(tag_lbl)

        badge_lbl = QLabel(STATUS_BADGE)
        badge_lbl.setStyleSheet("background: rgba(2,132,199,0.08); color: #0284C7; border: 1px solid rgba(2,132,199,0.25); padding: 4px 10px; border-radius: 10px; font-size: 9px; font-weight: 800; margin-top: 2px;")
        sb_layout.addWidget(badge_lbl)

        # Divider
        div1 = QFrame()
        div1.setFrameShape(QFrame.HLine)
        div1.setStyleSheet("border: none; background: #E2E8F0; height: 1px; margin: 4px 0;")
        sb_layout.addWidget(div1)

        # Nav List — Bright Glassy Selection Highlighting
        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet("""
            QListWidget { background: transparent; border: none; outline: none; }
            QListWidget::item {
                padding: 9px 12px;
                border-radius: 8px;
                color: #475569;
                font-weight: 700;
                font-size: 12px;
                margin-bottom: 2px;
                border-left: 3px solid transparent;
            }
            QListWidget::item:hover {
                background: rgba(2, 132, 199, 0.06);
                color: #0F172A;
            }
            QListWidget::item:selected {
                background: rgba(2, 132, 199, 0.12);
                color: #0284C7;
                font-weight: 900;
                border-left: 3px solid #0284C7;
            }
        """)

        nav_items = [
            "Overview",
            "Live Monitor",
            "Signal Lab",
            "Band Analysis",
            "Experiments",
            "Session Control",
            "Session Compare",
            "Reports & AI",
            "Validation Center",
            "Architecture",
            "History Archive",
            "Hardware Connection",
            "Results Platform",
            "Settings"
        ]

        for item in nav_items:
            self.nav_list.addItem(QListWidgetItem(item))

        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self.switch_screen)
        sb_layout.addWidget(self.nav_list)

        # Expo Demo Button
        btn_expo = QPushButton("⚡ PRESENTATION MODE")
        btn_expo.setStyleSheet("background: linear-gradient(135deg, #0284C7, #0369A1); color: white; font-weight: 800; font-size: 11px; padding: 10px; border-radius: 8px; border: none;")
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
        self.screen_hardware = HardwareScreen()
        self.screen_results = ResultsScreen()
        self.screen_settings = SettingsScreen()
        self.screen_presentation = PresentationModeScreen()
        self.screen_presentation.exit_presentation.connect(self.close_presentation_mode)

        # Connect hardware screen connection request signals
        self.screen_hardware.connect_port_requested.connect(self.connect_serial_port)
        self.screen_hardware.connect_wifi_requested.connect(self.connect_wifi_stream)
        self.screen_hardware.connect_pokidex_wifi_requested.connect(self.connect_pokidex_wifi)
        self.screen_hardware.connect_pokidex_ble_requested.connect(self.connect_pokidex_ble)
        self.screen_hardware.start_simulator_requested.connect(self.start_simulator)
        self.screen_hardware.disconnect_requested.connect(self.disconnect_all_hardware)

        # Connect Pokidex Manager signals
        self.pokidex_manager.sample_received.connect(self.on_pokidex_sample)
        self.pokidex_manager.wifi_connection_changed.connect(self.on_hardware_connection_changed)
        self.pokidex_manager.ble_connection_changed.connect(self.on_hardware_connection_changed)
        self.pokidex_manager.dual_telemetry_updated.connect(self.screen_hardware.update_dual_pokidex_telemetry)

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
        self.stacked_widget.addWidget(self.screen_hardware)       # 11
        self.stacked_widget.addWidget(self.screen_results)        # 12
        self.stacked_widget.addWidget(self.screen_settings)       # 13
        self.stacked_widget.addWidget(self.screen_presentation)   # 14

        main_layout.addWidget(self.stacked_widget)

    def switch_screen(self, row):
        if 0 <= row < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(row)

    def open_presentation_mode(self):
        self.sidebar.hide()
        self.stacked_widget.setCurrentIndex(14)
        self.showFullScreen()

    def close_presentation_mode(self):
        self.showNormal()
        self.sidebar.show()
        self.stacked_widget.setCurrentIndex(0)

    def connect_serial_port(self, port):
        self.disconnect_all_hardware()
        self.hw_serial_thread = HardwareSerialThread(target_port=port, baudrate=115200)
        self.hw_serial_thread.data_received.connect(self.on_hardware_data)
        self.hw_serial_thread.connection_changed.connect(self.on_hardware_connection_changed)
        self.hw_serial_thread.stats_updated.connect(self.screen_hardware.update_packet_stats)
        self.hw_serial_thread.start()

    def connect_wifi_stream(self, ip, port, protocol):
        self.disconnect_all_hardware()
        self.hw_wifi_thread = WifiStreamThread(ip=ip, port=port, protocol=protocol)
        self.hw_wifi_thread.data_received.connect(self.on_hardware_data)
        self.hw_wifi_thread.connection_changed.connect(self.on_hardware_connection_changed)
        self.hw_wifi_thread.stats_updated.connect(self.screen_hardware.update_packet_stats)
        self.hw_wifi_thread.start()

    def connect_pokidex_wifi(self, host, port):
        self.active_hardware_source = "POKIDEX"
        self.pokidex_manager.start_wifi_stream(host=host, port=port)

    def connect_pokidex_ble(self, address=None):
        self.active_hardware_source = "POKIDEX"
        self.pokidex_manager.start_ble_stream(address=address)

    def start_simulator(self):
        self.disconnect_all_hardware()
        self.active_hardware_source = "SIMULATOR"
        self.screen_hardware.set_hardware_status(True, "SIMULATOR ACTIVE (SYNTHETIC MODE)")

    def disconnect_all_hardware(self):
        if self.hw_serial_thread:
            self.hw_serial_thread.stop()
            self.hw_serial_thread = None
        if self.hw_wifi_thread:
            self.hw_wifi_thread.stop()
            self.hw_wifi_thread = None
        if self.pokidex_manager:
            self.pokidex_manager.stop_all()
        self.active_hardware_source = "IDLE"
        self.signal_buffer.clear()

    def on_hardware_data(self, val):
        self.active_hardware_source = "HARDWARE"
        self.signal_buffer.append(val)
        if len(self.signal_buffer) > 1250:
            self.signal_buffer = self.signal_buffer[-1250:]

    def on_pokidex_sample(self, val, frame_meta):
        self.active_hardware_source = "POKIDEX"
        self.signal_buffer.append(val)
        if len(self.signal_buffer) > 1250:
            self.signal_buffer = self.signal_buffer[-1250:]

    def on_hardware_connection_changed(self, is_connected, status_text):
        self.screen_hardware.set_hardware_status(is_connected, status_text)

    def init_dsp_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_dsp_frame)
        self.timer.start(40)  # 25 FPS update rate

    def process_dsp_frame(self):
        # Generate new synthetic chunk if hardware is not active
        if self.active_hardware_source == "SIMULATOR":
            chunk, _ = self.generator.generate_chunk(num_samples=10)
            self.signal_buffer.extend(chunk)
            if len(self.signal_buffer) > 1250:
                self.signal_buffer = self.signal_buffer[-1250:]

        signal_arr = np.array(self.signal_buffer)
        if len(signal_arr) < 32:
            return

        freqs, psd = self.psd_analyzer.compute_psd(signal_arr)
        band_powers = self.psd_analyzer.extract_band_powers(freqs, psd)
        metrics = self.psd_analyzer.compute_metrics(band_powers, freqs, psd)
        
        # Dual Classification
        rule_res = self.rule_classifier.classify(band_powers)
        ml_res = self.ml_classifier.predict(band_powers)

        metrics['load_class'] = rule_res['cognitive_state']
        metrics['rule_margin'] = rule_res['rule_margin']
        metrics['ml_confidence'] = ml_res['confidence']

        # Update active screens
        self.screen_overview.update_overview(signal_arr, band_powers, metrics)
        self.screen_monitor.update_monitor(signal_arr, freqs, psd)
        self.screen_signal_lab.update_lab_data(signal_arr)
        self.screen_results.update_results(band_powers, metrics, rule_res=rule_res, ml_res=ml_res)
        self.screen_presentation.update_presentation(signal_arr, metrics)
