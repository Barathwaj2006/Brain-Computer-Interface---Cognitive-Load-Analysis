"""
Hardware Serial Reader & Zero-Click Auto-Lock Engine
Scans USB COM ports in the background, validates packet integrity checksums,
detects the hardware sensor interface at 115200 baud / 250 Hz using NEUROSIM_HELLO,v1 handshake,
and locks onto the stream smoothly with zero user configuration.
"""

import time
import serial
import serial.tools.list_ports
from PySide6.QtCore import QThread, Signal

class HardwareSerialThread(QThread):
    data_received = Signal(float)
    connection_changed = Signal(bool, str)
    stats_updated = Signal(int, int, float)  # total, dropped, dropped_pct

    def __init__(self, target_port=None, baudrate=115200, allow_bare_fallback=False):
        super().__init__()
        self.target_port = target_port
        self.baudrate = baudrate
        self.allow_bare_fallback = allow_bare_fallback
        self.running = True
        self.is_connected = False
        self.active_port_name = "None"
        
        # Packet Integrity Metrics
        self.total_packets = 0
        self.dropped_packets = 0

    def auto_scan_and_connect(self):
        """
        Background USB serial auto-scanner.
        Requires exact 'NEUROSIM_HELLO,v1' handshake within timeout window.
        Falls back to legacy format only if self.allow_bare_fallback is True.
        """
        ports = serial.tools.list_ports.comports()
        for p in ports:
            try:
                ser = serial.Serial(p.device, self.baudrate, timeout=0.6)
                time.sleep(0.15)
                if ser.is_open:
                    # Read up to 5 lines to catch handshake
                    for _ in range(5):
                        if ser.in_waiting > 0:
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            if "NEUROSIM_HELLO,v1" in line:
                                ser.close()
                                return p.device
                            if self.allow_bare_fallback and (line.startswith("SAMPLE") or line.replace('.', '', 1).replace('-', '', 1).isdigit()):
                                ser.close()
                                return p.device
                    ser.close()
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

    def parse_line(self, line: str):
        """
        Parses incoming serial packet line and validates packet checksum integrity.
        Expected Format: SAMPLE,<value>,<sequence_number>,<checksum>
        """
        if not line:
            return None

        self.total_packets += 1

        parts = line.split(",")

        # Format: SAMPLE,<value>,<sequence_number>,<checksum>
        if len(parts) == 4 and parts[0] == "SAMPLE":
            try:
                val = float(parts[1])
                seq = int(parts[2])
                chk = int(parts[3])
                
                expected_chk = (seq + int(abs(val) * 100.0)) % 256
                
                if chk != expected_chk:
                    self.dropped_packets += 1
                    pct = (self.dropped_packets / max(1, self.total_packets)) * 100.0
                    self.stats_updated.emit(self.total_packets, self.dropped_packets, pct)
                    print(f"[SerialReader WARNING] Checksum mismatch! Recv: {chk}, Expected: {expected_chk}. Dropped: {self.dropped_packets}/{self.total_packets}")
                    return None
                
                pct = (self.dropped_packets / max(1, self.total_packets)) * 100.0
                self.stats_updated.emit(self.total_packets, self.dropped_packets, pct)
                return val
            except (ValueError, IndexError, TypeError):
                self.dropped_packets += 1
                pct = (self.dropped_packets / max(1, self.total_packets)) * 100.0
                self.stats_updated.emit(self.total_packets, self.dropped_packets, pct)
                return None

        # Fallback: SAMPLE,<value> (2 parts) or bare float
        try:
            if len(parts) == 2 and parts[0] == "SAMPLE":
                val = float(parts[1])
            elif len(parts) == 1:
                val = float(parts[0])
            else:
                self.dropped_packets += 1
                pct = (self.dropped_packets / max(1, self.total_packets)) * 100.0
                self.stats_updated.emit(self.total_packets, self.dropped_packets, pct)
                return None

            pct = (self.dropped_packets / max(1, self.total_packets)) * 100.0
            self.stats_updated.emit(self.total_packets, self.dropped_packets, pct)
            return val
        except ValueError:
            self.dropped_packets += 1
            pct = (self.dropped_packets / max(1, self.total_packets)) * 100.0
            self.stats_updated.emit(self.total_packets, self.dropped_packets, pct)
            return None

    def stop(self):
        self.running = False
        self.is_connected = False
        self.wait()
