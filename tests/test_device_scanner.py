"""
Unit Tests — Hardware Device Scanner & Wireless Network Discovery
Verifies:
- Bluetooth and Serial COM device scanning returns list format
- Wi-Fi network endpoint discovery parses host IP and UDP socket status
"""

import unittest
from src.acquisition.device_scanner import DeviceScanner, WifiStreamThread

class TestDeviceScanner(unittest.TestCase):
    def test_scan_bluetooth_and_serial_devices(self):
        devices = DeviceScanner.scan_bluetooth_and_serial_devices()
        self.assertIsInstance(devices, list)

    def test_scan_wifi_network_endpoints(self):
        endpoints = DeviceScanner.scan_wifi_network_endpoints(port=8080)
        self.assertIsInstance(endpoints, list)
        self.assertGreaterEqual(len(endpoints), 1)
        self.assertIn("ip", endpoints[0])
        self.assertIn("port", endpoints[0])

    def test_wifi_stream_parse_line(self):
        thread = WifiStreamThread(ip="0.0.0.0", port=8080, protocol="UDP")
        val = thread._parse_wifi_line("SAMPLE,24.5")
        self.assertEqual(val, 24.5)

        val_bare = thread._parse_wifi_line("18.2")
        self.assertEqual(val_bare, 18.2)

        val_bad = thread._parse_wifi_line("invalid_data")
        self.assertIsNone(val_bad)

if __name__ == '__main__':
    unittest.main()
