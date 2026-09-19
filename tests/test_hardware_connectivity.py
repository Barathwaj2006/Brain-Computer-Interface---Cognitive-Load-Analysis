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

    def test_paired_devices_structure(self):
        bt = self.mgr._detect_bluetooth_devices()
        if bt["paired_devices"]:
            first_dev = bt["paired_devices"][0]
            self.assertIn("name", first_dev)
            self.assertIn("mac", first_dev)
            self.assertIn("last_connected", first_dev)

if __name__ == '__main__':
    unittest.main()
