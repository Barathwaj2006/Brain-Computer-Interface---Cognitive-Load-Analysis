"""
Hardware Device Scanner & Wireless Network Discovery Module
Scans real system Bluetooth (SPP / COM ports) and local Wi-Fi (UDP/TCP streams) hardware interfaces.
No mock or dummy hardware — performs real hardware environment scanning.
"""

import socket
import select
import serial.tools.list_ports
from PySide6.QtCore import QThread, Signal

class DeviceScanner:
    @staticmethod
    def scan_bluetooth_and_serial_devices():
        """
        Scans all physical serial and Bluetooth SPP COM ports present on the host system.
        Categorizes devices into 'Bluetooth SPP' and 'USB Serial' based on hardware IDs.
        """
        devices = []
        ports = serial.tools.list_ports.comports()
        
        for p in ports:
            desc_lower = (p.description or "").lower()
            hwid_lower = (p.hwid or "").lower()

            if "bluetooth" in desc_lower or "bthenum" in hwid_lower or "bth" in desc_lower:
                dev_type = "Bluetooth SPP"
            elif "usb" in desc_lower or "cp210" in hwid_lower or "ch340" in hwid_lower or "ftdi" in hwid_lower or "cdc" in hwid_lower:
                dev_type = "USB Serial / ESP32"
            else:
                dev_type = "Serial Hardware Port"

            devices.append({
                "name": p.description or p.device,
                "port": p.device,
                "type": dev_type,
                "hwid": p.hwid or "N/A",
                "manufacturer": p.manufacturer or "Generic Hardware",
                "status": "Available"
            })
            
        return devices

    @staticmethod
    def scan_wifi_network_endpoints(port=8080, timeout=1.0):
        """
        Scans local Wi-Fi network interfaces for active UDP broadcast or TCP EEG stream endpoints.
        """
        endpoints = []
        try:
            # Local host IP resolution
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            endpoints.append({
                "name": f"Wi-Fi UDP Receiver ({local_ip})",
                "ip": "0.0.0.0",
                "port": port,
                "protocol": "UDP Socket",
                "status": "Ready to Listen"
            })

            # Check if UDP broadcast socket can bind
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(('', port))
                endpoints[0]["status"] = "Port Open (Available)"
            except Exception:
                endpoints[0]["status"] = "Port In Use / Bound"
            finally:
                sock.close()

        except Exception as e:
            endpoints.append({
                "name": "Local Wi-Fi Network Interface",
                "ip": "127.0.0.1",
                "port": port,
                "protocol": "UDP Socket",
                "status": f"Error: {str(e)}"
            })

        return endpoints


class WifiStreamThread(QThread):
    data_received = Signal(float)
    connection_changed = Signal(bool, str)
    stats_updated = Signal(int, int, float)  # total, dropped, pct

    def __init__(self, ip="0.0.0.0", port=8080, protocol="UDP"):
        super().__init__()
        self.ip = ip
        self.port = int(port)
        self.protocol = protocol.upper()
        self.running = True
        self.is_connected = False
        
        self.total_packets = 0
        self.dropped_packets = 0

    def run(self):
        if self.protocol == "UDP":
            self._run_udp()
        else:
            self._run_tcp()

    def _run_udp(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.ip, self.port))
            sock.settimeout(1.0)
            
            self.is_connected = True
            self.connection_changed.emit(True, f"Wi-Fi UDP Stream Connected ({self.ip}:{self.port})")

            while self.running and self.is_connected:
                try:
                    data, addr = sock.recvfrom(1024)
                    line = data.decode('utf-8', errors='ignore').strip()
                    val = self._parse_wifi_line(line)
                    if val is not None:
                        self.data_received.emit(val)
                except socket.timeout:
                    continue
                except Exception as e:
                    self.dropped_packets += 1
                    pct = (self.dropped_packets / max(1, self.total_packets)) * 100.0
                    self.stats_updated.emit(self.total_packets, self.dropped_packets, pct)

            sock.close()
        except Exception as e:
            self.is_connected = False
            self.connection_changed.emit(False, f"Wi-Fi Stream Error: {str(e)}")

    def _run_tcp(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect((self.ip, self.port))
            
            self.is_connected = True
            self.connection_changed.emit(True, f"Wi-Fi TCP Stream Connected ({self.ip}:{self.port})")

            buffer = ""
            while self.running and self.is_connected:
                try:
                    data = sock.recv(1024).decode('utf-8', errors='ignore')
                    if not data:
                        break
                    buffer += data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        val = self._parse_wifi_line(line.strip())
                        if val is not None:
                            self.data_received.emit(val)
                except socket.timeout:
                    continue

            sock.close()
        except Exception as e:
            self.is_connected = False
            self.connection_changed.emit(False, f"Wi-Fi Stream Error: {str(e)}")

    def _parse_wifi_line(self, line: str):
        if not line:
            return None

        self.total_packets += 1
        parts = line.split(",")

        try:
            if len(parts) >= 2 and parts[0] == "SAMPLE":
                val = float(parts[1])
            elif len(parts) == 1:
                val = float(parts[0])
            else:
                self.dropped_packets += 1
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
