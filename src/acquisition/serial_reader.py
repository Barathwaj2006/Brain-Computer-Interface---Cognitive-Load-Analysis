"""
Hardware Serial Reader & Zero-Click Auto-Lock Engine
Scans USB COM ports in the background, detects the hardware sensor interface at 115200 baud / 250 Hz,
and locks onto the stream smoothly with zero user configuration.
"""

import time
import serial
import serial.tools.list_ports
from PySide6.QtCore import QThread, Signal

class HardwareSerialThread(QThread):
    data_received = Signal(float)
    connection_changed = Signal(bool, str)

    def __init__(self, target_port=None, baudrate=115200):
        super().__init__()
        self.target_port = target_port
        self.baudrate = baudrate
        self.running = True
        self.is_connected = False
        self.active_port_name = "None"

    def auto_scan_and_connect(self):
        """
        Background USB serial auto-scanner.
        Attempts connection to available USB COM ports.
        """
        ports = serial.tools.list_ports.comports()
        for p in ports:
            try:
                ser = serial.Serial(p.device, self.baudrate, timeout=0.5)
                time.sleep(0.1)
                if ser.is_open:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    ser.close()
                    # Handshake check
                    if line.startswith("SAMPLE") or line.replace('.', '', 1).replace('-', '', 1).isdigit():
                        return p.device
            except Exception:
                continue
        return None

    def run(self):
        while self.running:
            if not self.is_connected:
                port_to_try = self.target_port or self.auto_scan_and_connect()
                if port_to_try:
                    try:
                        ser = serial.Serial(port_to_try, self.baudrate, timeout=1.0)
                        self.is_connected = True
                        self.active_port_name = port_to_try
                        self.connection_changed.emit(True, f"Hardware Connected ({port_to_try})")
                        
                        while self.running and self.is_connected:
                            if ser.in_waiting > 0:
                                line = ser.readline().decode('utf-8', errors='ignore').strip()
                                val = self.parse_line(line)
                                if val is not None:
                                    self.data_received.emit(val)
                            time.sleep(0.002)
                        
                        ser.close()
                    except Exception:
                        self.is_connected = False
                        self.connection_changed.emit(False, "Hardware Disconnected (Scanning...)")
                else:
                    time.sleep(1.0)  # Scan every 1 sec
            else:
                time.sleep(0.1)

    def parse_line(self, line):
        try:
            if line.startswith("SAMPLE,"):
                return float(line.split(",")[1])
            else:
                return float(line)
        except Exception:
            return None

    def stop(self):
        self.running = False
        self.is_connected = False
        self.wait()
