#!/usr/bin/env python3
"""
Unit and Integration Tests for Hardware Connectivity Module:
Validates real-time detection of host laptop Wi-Fi network and Bluetooth peripherals.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.acquisition.hardware_connectivity import HardwareConnectivityManager, connectivity_manager

class TestHardwareConnectivity(unittest.TestCase):
    def setUp(self):
        self.mgr = HardwareConnectivityManager()

    def test_singleton_instance_active(self):
        self.assertIsNotNone(connectivity_manager)
        status = connectivity_manager.get_status()
        self.assertIn("wifi", status)
        self.assertIn("bluetooth", status)

    def test_wifi_schema_and_types(self):
        wifi = self.mgr._detect_wifi_network()
        expected_keys = ["connected", "ssid", "signal", "radio_type", "band", "adapter", "state", "ip"]
        for key in expected_keys:
            self.assertIn(key, wifi, f"Missing key '{key}' in wifi status")
        self.assertIsInstance(wifi["connected"], bool)
        self.assertIsInstance(wifi["ssid"], str)
        self.assertIsInstance(wifi["ip"], str)

    def test_bluetooth_schema_and_types(self):
        bt = self.mgr._detect_bluetooth_devices()
        expected_keys = [
            "adapter_present", "adapter_name", "adapter_status",
            "connected_device", "connected_devices", "paired_devices", "bluetooth_ports"
        ]
        for key in expected_keys:
            self.assertIn(key, bt, f"Missing key '{key}' in bluetooth status")
        self.assertIsInstance(bt["adapter_present"], bool)
        self.assertIsInstance(bt["connected_devices"], list)
        self.assertIsInstance(bt["paired_devices"], list)

    def test_manual_device_pairing(self):
        st = self.mgr.set_connected_device("Noise Earbuds", "881e87a8decd")
        self.assertEqual(st["bluetooth"]["connected_device"], "Noise Earbuds")
        self.assertTrue(any(d["name"] == "Noise Earbuds" for d in st["bluetooth"]["connected_devices"]))

        st_disc = self.mgr.disconnect_device()
        self.assertIsNone(st_disc["bluetooth"]["connected_device"])

    def test_diagnostic_summary(self):
        diag = self.mgr.get_diagnostic_summary()
        self.assertIn("timestamp", diag)
        self.assertIn("wifi_telemetry", diag)
        self.assertIn("bluetooth_telemetry", diag)
        self.assertIn("adapter", diag["bluetooth_telemetry"])
        self.assertIn("top_paired_devices", diag["bluetooth_telemetry"])

if __name__ == '__main__':
    unittest.main()
