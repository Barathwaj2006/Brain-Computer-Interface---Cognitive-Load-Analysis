"""
Hardware Connection & Device Discovery Workstation Screen Module
Scans real system Bluetooth (SPP / Virtual COM), USB Serial, and local Wi-Fi network streams.
No made-up or fake hardware auto-connections.
Theme: Bright Frosted Glassmorphism
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QTabWidget
)
from PySide6.QtCore import Qt, Signal
from src.app.config import COLOR_CARD_BG, COLOR_CYAN, COLOR_EMERALD, COLOR_AMBER, COLOR_ROSE
from src.acquisition.device_scanner import DeviceScanner

class HardwareScreen(QWidget):
    connect_port_requested = Signal(str)        # Request connection to serial/bluetooth COM port
    connect_wifi_requested = Signal(str, int, str) # Request connection to Wi-Fi stream (ip, port, protocol)
    disconnect_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_connected = False
        self.active_device_name = "None"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header Title & Telemetry Badges
        header_card = QFrame()
        header_card.setStyleSheet("background: rgba(255, 255, 255, 0.85); border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px;")
        h_layout = QHBoxLayout(header_card)

        t_box = QVBoxLayout()
        title = QLabel("HARDWARE DEVICE SCANNER & CONNECTION CENTER")
        title.setStyleSheet("font-size: 15px; font-weight: 900; color: #0F172A; letter-spacing: 1px;")
        
        sub = QLabel("Real Bluetooth SPP • USB Serial COM Ports • Wi-Fi UDP/TCP Network Endpoints")
        sub.setStyleSheet("font-size: 11px; color: #64748B;")
        
        t_box.addWidget(title)
        t_box.addWidget(sub)
        h_layout.addLayout(t_box)
        h_layout.addStretch()

        self.stats_badge = QLabel("Packets: 0 | Dropped: 0 (0.0%)")
        self.stats_badge.setStyleSheet("background: rgba(2,132,199,0.08); color: #0284C7; border: 1px solid rgba(2,132,199,0.25); padding: 6px 12px; border-radius: 10px; font-weight: 700; font-size: 10px;")
        h_layout.addWidget(self.stats_badge)

        self.status_badge = QLabel("● DISCONNECTED (NO ACTIVE HARDWARE)")
        self.status_badge.setStyleSheet("background: rgba(239,68,68,0.12); color: #EF4444; border: 1px solid #EF4444; padding: 6px 14px; border-radius: 12px; font-weight: 800; font-size: 11px;")
        h_layout.addWidget(self.status_badge)

        layout.addWidget(header_card)

        # Main Body: Tabs for Bluetooth/Serial vs Wi-Fi Stream + Terminal Log
        body_layout = QHBoxLayout()
        body_layout.setSpacing(16)

        # Left Panel: Tabbed Scanner (Bluetooth/Serial vs Wi-Fi)
        self.scanner_tabs = QTabWidget()
        self.scanner_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E2E8F0; border-radius: 10px; background: #FFFFFF; }
            QTabBar::tab { background: #F1F5F9; color: #64748B; font-weight: 800; font-size: 11px; padding: 8px 16px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
            QTabBar::tab:selected { background: #0284C7; color: #FFFFFF; }
        """)

        # Tab 1: Bluetooth & Serial Scanner
        tab_bt = QWidget()
        bt_layout = QVBoxLayout(tab_bt)
        bt_layout.setContentsMargins(14, 14, 14, 14)
        bt_layout.setSpacing(10)

        bt_header = QHBoxLayout()
        bt_title = QLabel("BLUETOOTH & SERIAL COM DEVICES")
        bt_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #0284C7; letter-spacing: 1px;")
        
        self.btn_scan_bt = QPushButton("🔍 SCAN DEVICES")
        self.btn_scan_bt.setStyleSheet("background: #0284C7; color: white; font-weight: 800; font-size: 11px; padding: 6px 14px; border-radius: 6px; border: none;")
        self.btn_scan_bt.setCursor(Qt.PointingHandCursor)
        self.btn_scan_bt.clicked.connect(self.scan_bluetooth_devices)

        bt_header.addWidget(bt_title)
        bt_header.addStretch()
        bt_header.addWidget(self.btn_scan_bt)
        bt_layout.addLayout(bt_header)

        self.table_bt = QTableWidget(0, 5)
        self.table_bt.setHorizontalHeaderLabels(["Device Name", "Type", "Port", "Hardware ID", "Action"])
        self.table_bt.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_bt.setStyleSheet("""
            QTableWidget { background: #FFFFFF; border: 1px solid #E2E8F0; gridline-color: #E2E8F0; color: #0F172A; font-size: 11px; border-radius: 6px; }
            QHeaderView::section { background: #F8FAFC; color: #475569; font-weight: 800; font-size: 10px; padding: 6px; border: none; border-bottom: 1px solid #E2E8F0; }
        """)
        bt_layout.addWidget(self.table_bt)

        self.scanner_tabs.addTab(tab_bt, "🔵 Bluetooth & Serial")

        # Tab 2: Wi-Fi Network Stream Scanner
        tab_wifi = QWidget()
        wf_layout = QVBoxLayout(tab_wifi)
        wf_layout.setContentsMargins(14, 14, 14, 14)
        wf_layout.setSpacing(12)

        wf_title = QLabel("WI-FI NETWORK EEG STREAM ENDPOINT")
        wf_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #0284C7; letter-spacing: 1px;")
        wf_layout.addWidget(wf_title)

        # Wi-Fi Config Form
        form_frame = QFrame()
        form_frame.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px;")
        f_layout = QVBoxLayout(form_frame)
        f_layout.setSpacing(8)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel("IP Address:"))
        self.txt_wifi_ip = QLineEdit("0.0.0.0")
        self.txt_wifi_ip.setPlaceholderText("e.g. 192.168.1.100 or 0.0.0.0 for broadcast")
        self.txt_wifi_ip.setStyleSheet("background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; padding: 5px; border-radius: 4px; font-size: 11px;")
        r1.addWidget(self.txt_wifi_ip)
        f_layout.addLayout(r1)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Port:"))
        self.txt_wifi_port = QLineEdit("8080")
        self.txt_wifi_port.setStyleSheet("background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; padding: 5px; border-radius: 4px; font-size: 11px;")
        r2.addWidget(self.txt_wifi_port)

        r2.addWidget(QLabel("Protocol:"))
        self.combo_wifi_proto = QComboBox()
        self.combo_wifi_proto.addItems(["UDP Socket", "TCP Stream"])
        self.combo_wifi_proto.setStyleSheet("background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; padding: 5px; border-radius: 4px; font-size: 11px;")
        r2.addWidget(self.combo_wifi_proto)
        f_layout.addLayout(r2)

        wf_layout.addWidget(form_frame)

        wf_btn_layout = QHBoxLayout()
        self.btn_scan_wifi = QPushButton("📡 DISCOVER LOCAL NETWORK")
        self.btn_scan_wifi.setStyleSheet("background: #F1F5F9; color: #0F172A; font-weight: 700; font-size: 11px; padding: 8px 14px; border-radius: 6px; border: 1px solid #CBD5E1;")
        self.btn_scan_wifi.clicked.connect(self.scan_wifi_endpoints)

        self.btn_connect_wifi = QPushButton("⚡ CONNECT WI-FI STREAM")
        self.btn_connect_wifi.setStyleSheet("background: #0284C7; color: white; font-weight: 800; font-size: 11px; padding: 8px 14px; border-radius: 6px; border: none;")
        self.btn_connect_wifi.clicked.connect(self.connect_wifi_stream)

        wf_btn_layout.addWidget(self.btn_scan_wifi)
        wf_btn_layout.addWidget(self.btn_connect_wifi)
        wf_layout.addLayout(wf_btn_layout)

        wf_layout.addStretch()
        self.scanner_tabs.addTab(tab_wifi, "📶 Wi-Fi Stream")

        body_layout.addWidget(self.scanner_tabs, stretch=3)

        # Right Panel: Live Terminal Monitor
        term_card = QFrame()
        term_card.setStyleSheet("background: rgba(255, 255, 255, 0.85); border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px;")
        t_layout = QVBoxLayout(term_card)

        t_title = QLabel("HARDWARE TERMINAL LOG")
        t_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #0284C7; letter-spacing: 1px;")
        t_layout.addWidget(t_title)

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("background: #0F172A; color: #38BDF8; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; border: 1px solid #334155; border-radius: 8px;")
        self.terminal.setText("[SYSTEM] Hardware Connection Center Ready.\n[SYSTEM] No device automatically forced. Click SCAN to discover Bluetooth / USB / Wi-Fi devices.")
        t_layout.addWidget(self.terminal)

        # Disconnect Action Button
        self.btn_disconnect = QPushButton("✖ DISCONNECT HARDWARE")
        self.btn_disconnect.setStyleSheet("background: rgba(239, 68, 68, 0.15); color: #E11D48; border: 1px solid #E11D48; font-weight: 800; font-size: 11px; padding: 8px; border-radius: 6px;")
        self.btn_disconnect.clicked.connect(self.disconnect_hardware)
        t_layout.addWidget(self.btn_disconnect)

        body_layout.addWidget(term_card, stretch=2)

        layout.addLayout(body_layout)
        
        # Run initial scan on startup
        self.scan_bluetooth_devices()

    def scan_bluetooth_devices(self):
        self.terminal.append("[SCAN] Scanning host system for Bluetooth SPP and USB Serial devices...")
        devices = DeviceScanner.scan_bluetooth_and_serial_devices()
        
        self.table_bt.setRowCount(len(devices))
        if len(devices) == 0:
            self.terminal.append("[SCAN] No physical Bluetooth or USB Serial devices found on host system.")
            return

        for row, dev in enumerate(devices):
            self.table_bt.setItem(row, 0, QTableWidgetItem(dev['name']))
            self.table_bt.setItem(row, 1, QTableWidgetItem(dev['type']))
            self.table_bt.setItem(row, 2, QTableWidgetItem(dev['port']))
            self.table_bt.setItem(row, 3, QTableWidgetItem(dev['hwid'][:25]))

            btn_conn = QPushButton("CONNECT")
            btn_conn.setStyleSheet("background: #0284C7; color: white; font-weight: bold; font-size: 10px; padding: 4px 8px; border-radius: 4px; border: none;")
            btn_conn.clicked.connect(lambda _, p=dev['port'], n=dev['name']: self.connect_serial_device(p, n))
            self.table_bt.setCellWidget(row, 4, btn_conn)

        self.terminal.append(f"[SCAN] Found {len(devices)} physical hardware COM port(s).")

    def scan_wifi_endpoints(self):
        self.terminal.append("[SCAN] Discovering local Wi-Fi network endpoints...")
        port = int(self.txt_wifi_port.text()) if self.txt_wifi_port.text().isdigit() else 8080
        endpoints = DeviceScanner.scan_wifi_network_endpoints(port=port)
        for ep in endpoints:
            self.terminal.append(f"[WI-FI] Endpoint: {ep['name']} | IP: {ep['ip']}:{ep['port']} | Status: {ep['status']}")

    def connect_serial_device(self, port, name):
        self.active_device_name = f"{name} ({port})"
        self.terminal.append(f"[CONNECT] Attempting connection to {self.active_device_name}...")
        self.connect_port_requested.emit(port)

    def connect_wifi_stream(self):
        ip = self.txt_wifi_ip.text().strip() or "0.0.0.0"
        port = int(self.txt_wifi_port.text()) if self.txt_wifi_port.text().isdigit() else 8080
        proto = "UDP" if "UDP" in self.combo_wifi_proto.currentText() else "TCP"
        self.active_device_name = f"Wi-Fi {proto} ({ip}:{port})"
        self.terminal.append(f"[CONNECT] Connecting to {self.active_device_name}...")
        self.connect_wifi_requested.emit(ip, port, proto)

    def disconnect_hardware(self):
        self.terminal.append("[DISCONNECT] Disconnecting active hardware interface...")
        self.disconnect_requested.emit()
        self.set_hardware_status(False, "DISCONNECTED (USER REQUEST)")

    def update_packet_stats(self, total, dropped, pct):
        self.stats_badge.setText(f"Packets: {total} | Dropped: {dropped} ({pct:.1f}%)")

    def set_hardware_status(self, is_connected, status_text):
        self.is_connected = is_connected
        if is_connected:
            self.status_badge.setText(f"● {status_text}")
            self.status_badge.setStyleSheet("background: rgba(5,150,105,0.12); color: #059669; border: 1px solid #059669; padding: 6px 14px; border-radius: 12px; font-weight: 800; font-size: 11px;")
        else:
            self.status_badge.setText(f"● {status_text}")
            self.status_badge.setStyleSheet("background: rgba(239,68,68,0.12); color: #EF4444; border: 1px solid #EF4444; padding: 6px 14px; border-radius: 12px; font-weight: 800; font-size: 11px;")
