"""
Main Window Controller (PySide6 QMainWindow)
Coordinates sidebar navigation, screen switching across all 9 UI screens,
background signal acquisition, real-time DSP, classification, and session logging.
"""

import time
import datetime
import numpy as np
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QPushButton, QLabel, QFrame, QMessageBox
)
from PySide6.QtCore import QTimer, Qt, QThread, Signal
from PySide6.QtGui import QIcon, QFont, QColor

from src.app.config import APP_NAME, APP_SUBTITLE, COLORS, BUFFER_CAPACITY, SAMPLING_RATE_HZ, WINDOW_SAMPLES
from src.simulation.eeg_generator import SyntheticEEGGenerator
from src.acquisition.serial_reader import HardwareSerialThread
from src.processing.filter import EEGFilter
from src.processing.psd import PSDAnalyzer
from src.classification.rule_classifier import RuleBasedClassifier
from src.classification.ml_classifier import MLClassifier
from src.database.db_manager import DatabaseManager

# Import all 9 UI Screens
from src.ui.screens.splash_screen import SplashScreen
from src.ui.screens.home_screen import HomeScreen
from src.ui.screens.live_monitor_screen import LiveMonitorScreen
from src.ui.screens.band_analysis_screen import BandAnalysisScreen
from src.ui.screens.session_screen import SessionScreen
from src.ui.screens.summary_screen import SummaryScreen
from src.ui.screens.report_screen import ReportScreen
from src.ui.screens.history_screen import HistoryScreen
from src.ui.screens.settings_screen import SettingsScreen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — {APP_SUBTITLE}")
        self.resize(1280, 800)

        # State Variables
        self.mode = "SIMULATION"  # 'SIMULATION' or 'HARDWARE'
        self.is_recording = False
        self.recording_start_time = 0.0
        self.current_session_id = ""
        self.logged_samples_count = 0
        self.esp32_connected = False
        self.active_classifier_mode = "RULE"  # 'RULE' or 'ML'

        # Signal Buffers & Engines
        self.raw_buffer = np.zeros(BUFFER_CAPACITY, dtype=np.float64)
        self.buffer_idx = 0

        self.sim_generator = SyntheticEEGGenerator(sampling_rate=SAMPLING_RATE_HZ)
        self.hw_thread = None

        self.dsp_filter = EEGFilter(sampling_rate=SAMPLING_RATE_HZ)
        self.psd_analyzer = PSDAnalyzer(sampling_rate=SAMPLING_RATE_HZ)
        self.rule_classifier = RuleBasedClassifier()
        self.ml_classifier = MLClassifier()
        self.db = DatabaseManager()

        self.latest_psd_metrics = {}
        self.latest_class_res = {}
        self.session_snapshots = []

        # UI Setup
        self._init_ui()

        # Data Stream Timer (100ms interval -> 25 samples generated per tick in Simulation Mode)
        self.stream_timer = QTimer(self)
        self.stream_timer.timeout.connect(self._on_stream_tick)
        self.stream_timer.start(100)

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar Navigation Widget
        self.sidebar = QWidget()
        self.sidebar.setObjectName("SidebarWidget")
        self.sidebar.setFixedWidth(220)

        sb_layout = QVBoxLayout(self.sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Sidebar Header Logo
        logo_card = QFrame()
        logo_card.setStyleSheet("background-color: #0F172A; border-bottom: 1px solid #1E293B;")
        logo_layout = QVBoxLayout(logo_card)
        logo_layout.setContentsMargins(16, 16, 16, 16)

        logo_title = QLabel(APP_NAME)
        logo_title.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {COLORS['accent_cyan']}; letter-spacing: 2px;")
        logo_sub = QLabel("COGNITIVE ANALYSIS")
        logo_sub.setStyleSheet(f"font-size: 9px; font-weight: bold; color: {COLORS['text_muted']}; letter-spacing: 1px;")

        logo_layout.addWidget(logo_title)
        logo_layout.addWidget(logo_sub)
        sb_layout.addWidget(logo_card)

        # Navigation Buttons
        self.nav_buttons = {}
        nav_items = [
            ('home', '🏠 Home Dashboard'),
            ('monitor', '📈 Live Monitor'),
            ('band', '📊 Band Analysis'),
            ('session', '🔴 Session Control'),
            ('summary', '📑 Post Summary'),
            ('report', '📄 PDF Report'),
            ('history', '📁 History Archive'),
            ('settings', '⚙ Settings')
        ]

        for screen_key, label_text in nav_items:
            btn = QPushButton(label_text)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, k=screen_key: self.navigate_to(k))
            sb_layout.addWidget(btn)
            self.nav_buttons[screen_key] = btn

        sb_layout.addStretch()
        main_layout.addWidget(self.sidebar)

        # Main Screen Stack
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, stretch=1)

        # Instantiate Screens
        self.screen_splash = SplashScreen()
        self.screen_home = HomeScreen()
        self.screen_monitor = LiveMonitorScreen()
        self.screen_band = BandAnalysisScreen()
        self.screen_session = SessionScreen()
        self.screen_summary = SummaryScreen()
        self.screen_report = ReportScreen()
        self.screen_history = HistoryScreen()
        self.screen_settings = SettingsScreen()

        # Add to stack
        self.stack.addWidget(self.screen_splash)     # 0
        self.stack.addWidget(self.screen_home)       # 1
        self.stack.addWidget(self.screen_monitor)    # 2
        self.stack.addWidget(self.screen_band)       # 3
        self.stack.addWidget(self.screen_session)    # 4
        self.stack.addWidget(self.screen_summary)    # 5
        self.stack.addWidget(self.screen_report)     # 6
        self.stack.addWidget(self.screen_history)    # 7
        self.stack.addWidget(self.screen_settings)   # 8

        # Initially show Splash Screen (Hide sidebar on splash)
        self.sidebar.setVisible(False)
        self.stack.setCurrentIndex(0)

        # Connect Screen Signals
        self.screen_splash.start_requested.connect(lambda: self.navigate_to('home'))

        self.screen_home.start_session_requested.connect(self._start_recording_session)
        self.screen_home.set_mode_requested.connect(self._set_mode)
        self.screen_home.nav_requested.connect(self.navigate_to)

        self.screen_session.start_session_signal.connect(self._start_recording_session)
        self.screen_session.stop_session_signal.connect(self._stop_recording_session)

        self.screen_summary.generate_report_requested.connect(lambda: self.navigate_to('report'))

        self.screen_history.open_session_requested.connect(self._open_history_session)

        self.screen_settings.sim_params_changed.connect(self.sim_generator.set_amplitudes)
        self.screen_settings.classifier_changed.connect(self._set_classifier_mode)
        self.screen_settings.com_changed.connect(self._reconnect_hardware)

    def navigate_to(self, screen_key: str):
        mapping = {
            'home': 1, 'monitor': 2, 'band': 3, 'session': 4,
            'summary': 5, 'report': 6, 'history': 7, 'settings': 8
        }
        if screen_key in mapping:
            self.sidebar.setVisible(True)
            self.stack.setCurrentIndex(mapping[screen_key])

            # Update checked nav button
            for k, btn in self.nav_buttons.items():
                btn.setChecked(k == screen_key)

            if screen_key == 'history':
                self.screen_history.load_history()

    def _set_mode(self, new_mode: str):
        self.mode = new_mode
        if new_mode == "HARDWARE":
            self._start_hardware_thread()
        else:
            self._stop_hardware_thread()
            self.esp32_connected = False

        self.screen_home.update_system_status(self.mode == "HARDWARE", self.esp32_connected, self.is_recording)

    def _start_hardware_thread(self, port="AUTO", baud=115200):
        self._stop_hardware_thread()
        self.hw_thread = HardwareSerialThread(port=port, baud_rate=baud, parent=self)
        self.hw_thread.data_received.connect(self._on_hardware_data)
        self.hw_thread.connection_status.connect(self._on_hw_status)
        self.hw_thread.start()

    def _stop_hardware_thread(self):
        if self.hw_thread and self.hw_thread.isRunning():
            self.hw_thread.stop()
            self.hw_thread = None

    def _on_hw_status(self, msg: str, is_connected: bool):
        self.esp32_connected = is_connected
        self.screen_home.update_system_status(self.mode == "HARDWARE", self.esp32_connected, self.is_recording)

    def _reconnect_hardware(self, port: str, baud: int):
        if self.mode == "HARDWARE":
            self._start_hardware_thread(port, baud)

    def _set_classifier_mode(self, mode_str: str):
        self.active_classifier_mode = mode_str

    def _on_stream_tick(self):
        """Simulation mode stream generator (250Hz target = 25 samples per 100ms)."""
        if self.mode == "SIMULATION":
            chunk, _ = self.sim_generator.generate_chunk(25)
            self._process_eeg_chunk(chunk)

    def _on_hardware_data(self, chunk: np.ndarray, info: dict):
        """Callback for hardware serial thread stream."""
        if self.mode == "HARDWARE":
            self._process_eeg_chunk(chunk)

    def _process_eeg_chunk(self, chunk: np.ndarray):
        """Append chunk to ring buffer, run DSP filtering, PSD analysis, & update UI."""
        n = len(chunk)
        if n == 0:
            return

        # Roll buffer & insert new chunk
        self.raw_buffer = np.roll(self.raw_buffer, -n)
        self.raw_buffer[-n:] = chunk

        if self.is_recording:
            self.logged_samples_count += n

        # Run DSP Pipeline over 5 sec window (1250 samples)
        window = self.raw_buffer[-WINDOW_SAMPLES:]
        filtered = self.dsp_filter.process(window)
        freqs, psd = self.psd_analyzer.compute_psd(filtered)
        metrics = self.psd_analyzer.analyze_bands(freqs, psd)

        # Run Classifier
        if self.active_classifier_mode == 'ML':
            class_res = self.ml_classifier.predict(metrics)
        else:
            class_res = self.rule_classifier.classify(metrics)

        self.latest_psd_metrics = metrics
        self.latest_class_res = class_res

        if self.is_recording:
            self.session_snapshots.append((metrics, class_res))

        # Update Screens
        self.screen_monitor.update_live_data(filtered, freqs, psd, metrics, class_res)
        self.screen_band.update_metrics(metrics)

        # Update Session screen counters if active
        if self.is_recording:
            dur = time.time() - self.recording_start_time
            self.screen_session.update_session_info(
                self.current_session_id, dur, self.logged_samples_count, class_res.get('cognitive_state', 'MODERATE'), True
            )

    def _start_recording_session(self):
        self.is_recording = True
        self.recording_start_time = time.time()
        self.current_session_id = f"SESS-{int(time.time())}"
        self.logged_samples_count = 0
        self.session_snapshots = []

        self.screen_session.update_session_info(self.current_session_id, 0.0, 0, "RECORDING...", True)
        self.navigate_to('session')
        self.screen_home.update_system_status(self.mode == "HARDWARE", self.esp32_connected, True)

    def _stop_recording_session(self):
        if not self.is_recording:
            return

        self.is_recording = False
        duration = time.time() - self.recording_start_time

        # Calculate average session band activity & stress metrics
        if self.session_snapshots:
            avg_delta = np.mean([s[0]['rel_powers']['delta'] for s in self.session_snapshots])
            avg_theta = np.mean([s[0]['rel_powers']['theta'] for s in self.session_snapshots])
            avg_alpha = np.mean([s[0]['rel_powers']['alpha'] for s in self.session_snapshots])
            avg_beta  = np.mean([s[0]['rel_powers']['beta']  for s in self.session_snapshots])
            avg_stress = np.mean([s[0]['stress_index'] for s in self.session_snapshots])

            states = [s[1]['cognitive_state'] for s in self.session_snapshots]
            dom_state = max(set(states), key=states.count)
        else:
            avg_delta, avg_theta, avg_alpha, avg_beta, avg_stress, dom_state = 25.0, 25.0, 25.0, 25.0, 0.5, 'MODERATE'

        session_record = {
            'session_id': self.current_session_id,
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'duration': duration,
            'sampling_rate': SAMPLING_RATE_HZ,
            'mode': self.mode,
            'rel_delta': float(avg_delta),
            'rel_theta': float(avg_theta),
            'rel_alpha': float(avg_alpha),
            'rel_beta': float(avg_beta),
            'dominant_band': self.latest_psd_metrics.get('dominant_band', 'ALPHA'),
            'cognitive_state': dom_state,
            'stress_index': float(avg_stress),
            'confidence': float(self.latest_class_res.get('confidence', 85.0)),
            'notes': 'Recorded Synthetic EEG Session'
        }

        # Save to SQLite Database
        self.db.save_session(session_record)

        self.screen_summary.set_summary_data(session_record)
        self.screen_report.set_session(session_record)
        self.screen_home.update_system_status(self.mode == "HARDWARE", self.esp32_connected, False)
        self.navigate_to('summary')

    def _open_history_session(self, sess_data: dict):
        self.screen_summary.set_summary_data(sess_data)
        self.screen_report.set_session(sess_data)
        self.navigate_to('summary')

    def closeEvent(self, event):
        self._stop_hardware_thread()
        event.accept()
