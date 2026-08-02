"""
Hardware Connection & Digital Workstation Screen Module ("Care" Style CAD Terminal)
Displays:
- Connection Status Panel (CONNECTED vs DISCONNECTED)
- Interactive Digital Potentiometer Control Array (Delta 2Hz, Theta 6Hz, Alpha 10Hz, Beta 20Hz)
- Real-time Voltage (0.00V - 3.30V) and ADC (0 - 4095) readouts
- Serial Data Packet Terminal Stream
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSlider, QTextEdit, QPushButton, QGridLayout
from PySide6.QtCore import Qt, Signal
from src.app.config import COLOR_CARD_BG, COLOR_CYAN, COLOR_EMERALD, COLOR_AMBER, COLOR_ROSE

class HardwareScreen(QWidget):
    sim_params_changed = Signal(float, float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_connected = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header Title & Status
        header_card = QFrame()
        header_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px;")
        h_layout = QHBoxLayout(header_card)

        t_box = QVBoxLayout()
        title = QLabel("HARDWARE CONNECTION DIAGNOSTICS & VIRTUAL TERMINAL")
        title.setStyleSheet("font-size: 15px; font-weight: 900; color: #F8FAFC; letter-spacing: 1px;")
        
        sub = QLabel("Care Biomedical Workstation Engine • 115200 Baud • 250 Hz USB Serial Stream")
        sub.setStyleSheet("font-size: 11px; color: #94A3B8;")
        
        t_box.addWidget(title)
        t_box.addWidget(sub)
        h_layout.addLayout(t_box)
        h_layout.addStretch()

        self.status_badge = QLabel("● HARDWARE CONNECTED (AUTO-LOCK)")
        self.status_badge.setStyleSheet("background: rgba(16,185,129,0.15); color: #10B981; border: 1px solid #10B981; padding: 6px 14px; border-radius: 12px; font-weight: 800; font-size: 11px;")
        h_layout.addWidget(self.status_badge)

        layout.addWidget(header_card)

        # Main Split: Left Potentiometers Array + Right Terminal
        main_grid = QHBoxLayout()
        main_grid.setSpacing(16)

        # Left: Interactive Digital Potentiometer Control Array
        pots_card = QFrame()
        pots_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px;")
        p_layout = QVBoxLayout(pots_card)

        p_title = QLabel("NEURAL SENSOR POTENTIOMETER CONTROLS")
        p_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #06B6D4; letter-spacing: 1px; margin-bottom: 12px;")
        p_layout.addWidget(p_title)

        self.sld_delta, self.val_delta_v, self.val_delta_adc = self._create_pot_control("POT 1: DELTA (2 Hz)", 30, p_layout)
        self.sld_theta, self.val_theta_v, self.val_theta_adc = self._create_pot_control("POT 2: THETA (6 Hz)", 40, p_layout)
        self.sld_alpha, self.val_alpha_v, self.val_alpha_adc = self._create_pot_control("POT 3: ALPHA (10 Hz)", 80, p_layout)
        self.sld_beta,  self.val_beta_v,  self.val_beta_adc  = self._create_pot_control("POT 4: BETA (20 Hz)", 30, p_layout)

        main_grid.addWidget(pots_card, stretch=3)

        # Right: Live Serial Terminal Stream Monitor
        term_card = QFrame()
        term_card.setStyleSheet(f"background: {COLOR_CARD_BG}; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px;")
        t_layout = QVBoxLayout(term_card)

        t_title = QLabel("SERIAL PACKET TERMINAL MONITOR")
        t_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #06B6D4; letter-spacing: 1px;")
        t_layout.addWidget(t_title)

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("background: #0B0F19; color: #10B981; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px;")
        self.terminal.setText("[00:00:01] USB Serial Auto-Scanner Initialized...\n[00:00:01] Listening on 115200 Baud...\n[00:00:02] SAMPLE, 1.65 V | ADC: 2048 | 250Hz Sync OK\n[00:00:02] SAMPLE, 1.68 V | ADC: 2085 | 250Hz Sync OK\n[00:00:03] SAMPLE, 1.72 V | ADC: 2135 | 250Hz Sync OK")
        
        t_layout.addWidget(self.terminal)
        main_grid.addWidget(term_card, stretch=2)

        layout.addLayout(main_grid)

    def _create_pot_control(self, title, default_val, parent_layout):
        row_frame = QFrame()
        row_frame.setStyleSheet("background: rgba(15,23,42,0.8); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 10px;")
        l = QVBoxLayout(row_frame)
        l.setSpacing(6)

        header = QHBoxLayout()
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 11px; font-weight: 800; color: #F8FAFC;")
        
        v_lbl = QLabel(f"{(default_val / 100.0) * 3.3:.2f} V")
        v_lbl.setStyleSheet("font-size: 12px; font-weight: 900; color: #06B6D4;")

        adc_lbl = QLabel(f"ADC: {int((default_val / 100.0) * 4095)}")
        adc_lbl.setStyleSheet("font-size: 10px; color: #94A3B8;")

        header.addWidget(t_lbl)
        header.addStretch()
        header.addWidget(v_lbl)
        header.addWidget(adc_lbl)
        l.addLayout(header)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(default_val)
        slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 6px; background: #0B0F19; border-radius: 3px; }
            QSlider::sub-page:horizontal { background: #06B6D4; border-radius: 3px; }
            QSlider::handle:horizontal { background: #F8FAFC; border: 2px solid #06B6D4; width: 14px; height: 14px; margin: -4px 0; border-radius: 7px; }
        """)
        
        slider.valueChanged.connect(lambda val, vl=v_lbl, al=adc_lbl: self.on_slider_changed(val, vl, al))
        l.addWidget(slider)

        parent_layout.addWidget(row_frame)
        return slider, v_lbl, adc_lbl

    def on_slider_changed(self, val, v_lbl, adc_lbl):
        v = (val / 100.0) * 3.3
        adc = int((val / 100.0) * 4095)
        v_lbl.setText(f"{v:.2f} V")
        adc_lbl.setText(f"ADC: {adc}")

        # Emit updated values
        self.sim_params_changed.emit(
            self.sld_delta.value() / 100.0,
            self.sld_theta.value() / 100.0,
            self.sld_alpha.value() / 100.0,
            self.sld_beta.value() / 100.0
        )

        # Log to terminal
        self.terminal.append(f"[LIVE] Potentiometer Input Changed -> Voltage: {v:.2f}V | ADC: {adc}")

    def set_hardware_status(self, is_connected, status_text):
        self.is_connected = is_connected
        if is_connected:
            self.status_badge.setText(f"● {status_text}")
            self.status_badge.setStyleSheet("background: rgba(16,185,129,0.15); color: #10B981; border: 1px solid #10B981; padding: 6px 14px; border-radius: 12px; font-weight: 800; font-size: 11px;")
        else:
            self.status_badge.setText(f"● {status_text}")
            self.status_badge.setStyleSheet("background: rgba(245,158,11,0.15); color: #F59E0B; border: 1px solid #F59E0B; padding: 6px 14px; border-radius: 12px; font-weight: 800; font-size: 11px;")
