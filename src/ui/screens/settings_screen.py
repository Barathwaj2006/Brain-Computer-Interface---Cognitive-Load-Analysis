"""
Screen 9 — Configuration & Simulation Settings Screen
Configure hardware COM ports, baud rate, classifier mode, noise level, and live waveform sliders.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider, QRadioButton, QButtonGroup, QPushButton
)
from PySide6.QtCore import Qt, Signal
from src.app.config import COLORS
from src.visualization.custom_widgets import GlassCard
from src.acquisition.serial_reader import HardwareSerialThread

class SettingsScreen(QWidget):
    sim_params_changed = Signal(float, float, float, float, float)  # (d, t, a, b, noise)
    classifier_changed = Signal(str)                                # 'RULE' or 'ML'
    com_changed = Signal(str, int)                                  # (port, baud)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("SYSTEM CONFIGURATION & SIMULATION CONTROLS")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        layout.addWidget(title)

        # 1. Simulation Waveform Controls Card
        sim_card = GlassCard()
        sim_layout = QVBoxLayout(sim_card)
        sim_layout.setContentsMargins(20, 16, 20, 16)

        sim_title = QLabel("SYNTHETIC EEG WAVEFORM CONTROLS (SIMULATION MODE)")
        sim_title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {COLORS['text_muted']}; letter-spacing: 1px;")
        sim_layout.addWidget(sim_title)

        self.slider_d = self._create_slider_row(sim_layout, "Delta (2 Hz) Amplitude:", COLORS['accent_cyan'])
        self.slider_t = self._create_slider_row(sim_layout, "Theta (6 Hz) Amplitude:", COLORS['accent_emerald'])
        self.slider_a = self._create_slider_row(sim_layout, "Alpha (10 Hz) Amplitude:", COLORS['accent_purple'])
        self.slider_b = self._create_slider_row(sim_layout, "Beta (20 Hz) Amplitude:", COLORS['accent_amber'])
        self.slider_n = self._create_slider_row(sim_layout, "Gaussian Noise Level:", COLORS['accent_rose'])

        layout.addWidget(sim_card)

        # 2. Hardware COM Port Config Card
        hw_card = GlassCard()
        hw_layout = QVBoxLayout(hw_card)
        hw_layout.setContentsMargins(20, 16, 20, 16)

        hw_title = QLabel("HARDWARE SERIAL COMMUNICATION (ESP32)")
        hw_title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {COLORS['text_muted']}; letter-spacing: 1px;")
        hw_layout.addWidget(hw_title)

        com_row = QHBoxLayout()
        com_row.addWidget(QLabel("COM Port:"))
        
        self.combo_port = QComboBox()
        self.combo_port.addItem("AUTO")
        for p in HardwareSerialThread.get_available_ports():
            self.combo_port.addItem(p)
            
        com_row.addWidget(self.combo_port)

        com_row.addWidget(QLabel("Baud Rate:"))
        self.combo_baud = QComboBox()
        self.combo_baud.addItems(["115200", "9600", "57600", "230400"])
        com_row.addWidget(self.combo_baud)

        self.btn_refresh_com = QPushButton("🔄 SCAN PORTS")
        self.btn_refresh_com.setProperty("class", "SecondaryBtn")
        self.btn_refresh_com.clicked.connect(self._scan_ports)
        com_row.addWidget(self.btn_refresh_com)

        hw_layout.addLayout(com_row)
        layout.addWidget(hw_card)

        # 3. Classifier System Card
        class_card = GlassCard()
        class_layout = QVBoxLayout(class_card)
        class_layout.setContentsMargins(20, 16, 20, 16)

        class_title = QLabel("COGNITIVE LOAD CLASSIFIER SYSTEM")
        class_title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {COLORS['text_muted']}; letter-spacing: 1px;")
        class_layout.addWidget(class_title)

        class_row = QHBoxLayout()
        self.rb_rule = QRadioButton("Rule-Based Expert System (Clinical Decision Boundaries)")
        self.rb_ml   = QRadioButton("Machine Learning Model (Random Forest Classifier)")
        self.rb_rule.setChecked(True)

        self.class_grp = QButtonGroup(self)
        self.class_grp.addButton(self.rb_rule)
        self.class_grp.addButton(self.rb_ml)

        class_row.addWidget(self.rb_rule)
        class_row.addWidget(self.rb_ml)
        class_layout.addLayout(class_row)

        layout.addWidget(class_card)
        layout.addStretch()

        # Connect signals
        for s in [self.slider_d, self.slider_t, self.slider_a, self.slider_b, self.slider_n]:
            s.valueChanged.connect(self._emit_sim_params)

        self.class_grp.buttonClicked.connect(self._emit_classifier)
        self.combo_port.currentIndexChanged.connect(self._emit_com)
        self.combo_baud.currentIndexChanged.connect(self._emit_com)

    def _create_slider_row(self, parent_layout, label_text: str, color_hex: str) -> QSlider:
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setFixedWidth(180)
        lbl.setStyleSheet("font-size: 11px; font-weight: bold;")
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(50)
        
        val_lbl = QLabel("0.50")
        val_lbl.setFixedWidth(40)
        val_lbl.setStyleSheet(f"color: {color_hex}; font-weight: bold;")

        slider.valueChanged.connect(lambda v, l=val_lbl: l.setText(f"{v/100.0:.2f}"))

        row.addWidget(lbl)
        row.addWidget(slider)
        row.addWidget(val_lbl)
        parent_layout.addLayout(row)
        return slider

    def _scan_ports(self):
        self.combo_port.clear()
        self.combo_port.addItem("AUTO")
        for p in HardwareSerialThread.get_available_ports():
            self.combo_port.addItem(p)

    def _emit_sim_params(self):
        d = self.slider_d.value() / 100.0
        t = self.slider_t.value() / 100.0
        a = self.slider_a.value() / 100.0
        b = self.slider_b.value() / 100.0
        n = self.slider_n.value() / 100.0
        self.sim_params_changed.emit(d, t, a, b, n)

    def _emit_classifier(self):
        choice = 'ML' if self.rb_ml.isChecked() else 'RULE'
        self.classifier_changed.emit(choice)

    def _emit_com(self):
        port = self.combo_port.currentText()
        baud = int(self.combo_baud.currentText())
        self.com_changed.emit(port, baud)
