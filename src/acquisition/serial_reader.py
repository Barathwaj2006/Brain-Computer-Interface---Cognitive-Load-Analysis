"""
PySerial Hardware Data Acquisition Module
Auto-detects ESP32 COM port, streams synthetic EEG packets asynchronously,
handles disconnects gracefully, and emits signals to UI.
"""

import time
import serial
import serial.tools.list_ports
import numpy as np
from typing import List, Optional
from PySide6.QtCore import QThread, Signal
from src.app.config import DEFAULT_BAUD_RATE, SAMPLING_RATE_HZ

class HardwareSerialThread(QThread):
    data_received = Signal(np.ndarray, dict)  # (waveform_chunk, info_dict)
    connection_status = Signal(str, bool)     # (status_msg, is_connected)

    def __init__(self, port: str = "AUTO", baud_rate: int = DEFAULT_BAUD_RATE, parent=None):
        super().__init__(parent)
        self.port = port
        self.baud_rate = baud_rate
        self.is_running = False
        self.ser: Optional[serial.Serial] = None

    @staticmethod
    def get_available_ports() -> List[str]:
        """List available system COM ports."""
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports]

    @staticmethod
    def auto_detect_esp32_port() -> Optional[str]:
        """Auto-detect likely ESP32 / USB-Serial device."""
        ports = serial.tools.list_ports.comports()
        for p in ports:
            desc = p.description.lower()
            if any(k in desc for k in ['cp210', 'ch340', 'ftdi', 'usb serial', 'esp32', 'uart']):
                return p.device
        return ports[0].device if ports else None

    def run(self):
        self.is_running = True

        target_port = self.port
        if target_port == "AUTO":
            target_port = self.auto_detect_esp32_port()

        if not target_port:
            self.connection_status.emit("ESP32 DISCONNECTED (No COM Ports Found)", False)
            self.is_running = False
            return

        try:
            self.ser = serial.Serial(target_port, self.baud_rate, timeout=1.0)
            self.connection_status.emit(f"ESP32 CONNECTED ({target_port})", True)
        except Exception as e:
            self.connection_status.emit(f"ESP32 CONNECTION ERROR ({e})", False)
            self.is_running = False
            return

        buffer = []
        chunk_size = 25  # Send chunk every 100ms (25 samples at 250Hz)

        while self.is_running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if not line:
                        continue
                    
                    # Parse line format: "SAMPLE,<val>" or "<val>" or "P1,P2,P3,P4,<val>"
                    parts = line.split(',')
                    val = None
                    try:
                        val = float(parts[-1])
                    except ValueError:
                        continue

                    if val is not None:
                        buffer.append(val)

                    if len(buffer) >= chunk_size:
                        chunk = np.array(buffer, dtype=np.float64)
                        buffer = []
                        self.data_received.emit(chunk, {'source': 'HARDWARE', 'port': target_port})

                else:
                    time.sleep(0.01)

            except (serial.SerialException, OSError) as e:
                self.connection_status.emit(f"DEVICE DISCONNECTED ({e})", False)
                break
            except Exception as e:
                time.sleep(0.05)

        if self.ser and self.ser.is_open:
            self.ser.close()

    def stop(self):
        self.is_running = False
        self.wait(1000)
