"""
Phase 2 Connection Core Regression Tests for NeuroSim 2.0
Validates NormalizedFrame, BaseConnectionAdapter, Pokidex Wi-Fi/BLE Adapters, ESP32 Adapters,
SimulatorAdapter isolation, telemetry tracking, and disconnection safety.
"""

import unittest
import time
from PySide6.QtWidgets import QApplication
from src.app.state import CentralStateManager, ConnectionState, InputSource, ConnectionTelemetry
from src.processing.signal_buffer import BoundedSignalBuffer
from src.acquisition.contracts import NormalizedFrame, BaseConnectionAdapter
from src.acquisition.adapters import (
    PokidexWifiAdapter,
    PokidexBleAdapter,
    ESP32SerialAdapter,
    ESP32WifiAdapter,
    SimulatorAdapter
)
from src.acquisition.acquisition_manager import AcquisitionManager
from src.ui.main_window import MainWindow

app = QApplication.instance() or QApplication([])

class TestConnectionCore(unittest.TestCase):
    def setUp(self):
        self.state_mgr = CentralStateManager()
        self.buffer = BoundedSignalBuffer(capacity=100)
        self.acq_mgr = AcquisitionManager(self.state_mgr, self.buffer)

    def test_01_normalized_frame_schema(self):
        frame = NormalizedFrame(
            source=InputSource.POKIDEX_WIFI,
            transport="Wi-Fi WebSocket",
            device_id="Pokidex-Phone",
            sequence=10,
            sampling_rate=250,
            channel_count=1,
            data=[14.2, 18.5],
            events=[{"type": "STIMULUS"}],
            latency_ms=12.4,
            integrity_status="VALID"
        )
        self.assertEqual(frame.source, InputSource.POKIDEX_WIFI)
        self.assertEqual(frame.transport, "Wi-Fi WebSocket")
        self.assertEqual(frame.sequence, 10)
        self.assertEqual(len(frame.data), 2)
        self.assertEqual(frame.integrity_status, "VALID")

    def test_02_connection_telemetry_drop_percentage(self):
        telem = ConnectionTelemetry(packets_received=90, packets_dropped=10)
        telem.update_drop_percentage()
        self.assertEqual(telem.drop_percentage, 10.0)

    def test_03_pokidex_wifi_adapter_initialization(self):
        adapter = PokidexWifiAdapter(host="192.168.1.50", port=8765)
        self.assertEqual(adapter.source, InputSource.POKIDEX_WIFI)
        self.assertEqual(adapter.transport_name, "Wi-Fi WebSocket")
        self.assertEqual(adapter.status(), ConnectionState.IDLE)
        self.assertFalse(adapter.is_connected())

    def test_04_pokidex_ble_adapter_uuids(self):
        adapter = PokidexBleAdapter()
        self.assertEqual(adapter.source, InputSource.POKIDEX_BLE)
        self.assertEqual(adapter.transport_name, "BLE GATT")
        self.assertEqual(adapter.status(), ConnectionState.IDLE)

    def test_05_esp32_serial_adapter_initialization(self):
        adapter = ESP32SerialAdapter(port="COM4", baudrate=115200)
        self.assertEqual(adapter.source, InputSource.ESP32_USB)
        self.assertEqual(adapter.transport_name, "USB Serial")
        self.assertEqual(adapter.port, "COM4")

    def test_06_esp32_wifi_adapter_initialization(self):
        adapter = ESP32WifiAdapter(ip="192.168.1.100", port=8888, protocol="UDP")
        self.assertEqual(adapter.source, InputSource.ESP32_WIFI)
        self.assertEqual(adapter.transport_name, "Wi-Fi Stream")

    def test_07_simulator_adapter_isolation(self):
        adapter = SimulatorAdapter()
        self.assertEqual(adapter.source, InputSource.SIMULATOR)
        self.assertEqual(adapter.status(), ConnectionState.IDLE)
        self.assertFalse(adapter.is_streaming())

        # Generating chunk while IDLE returns empty list
        chunk = adapter.generate_chunk(10)
        self.assertEqual(len(chunk), 0)

        # Explicit connect + start_stream activates simulator
        adapter.connect_adapter()
        adapter.start_stream()
        self.assertTrue(adapter.is_streaming())

        chunk = adapter.generate_chunk(10)
        self.assertEqual(len(chunk), 10)

    def test_08_disconnection_safety_clears_buffer_and_state(self):
        self.acq_mgr.start_simulator()
        self.acq_mgr.generate_simulator_chunk(num_samples=20)
        self.assertGreater(len(self.buffer), 0)
        self.assertEqual(self.state_mgr.state, ConnectionState.STREAMING)

        # Disconnect safely
        self.acq_mgr.stop_all()
        self.assertEqual(self.state_mgr.state, ConnectionState.IDLE)
        self.assertEqual(self.state_mgr.source, InputSource.NONE)
        self.assertEqual(len(self.buffer), 0)

        # Verify no synthetic generation occurs after disconnect
        self.acq_mgr.generate_simulator_chunk(num_samples=10)
        self.assertEqual(len(self.buffer), 0)

    def test_09_illegal_state_transitions_rejected(self):
        sm = CentralStateManager()
        self.assertEqual(sm.state, ConnectionState.IDLE)
        
        # STREAMING directly from IDLE without connecting is allowed in matrix, but DISCONNECTING to STREAMING is illegal
        sm.transition_to(ConnectionState.CONNECTING)
        sm.transition_to(ConnectionState.DISCONNECTING)
        res = sm.transition_to(ConnectionState.STREAMING)
        self.assertFalse(res)
        self.assertEqual(sm.state, ConnectionState.DISCONNECTING)

    def test_10_mainwindow_telemetry_integration(self):
        win = MainWindow()
        self.assertEqual(win.state_manager.state, ConnectionState.IDLE)
        win.start_simulator()
        self.assertEqual(win.state_manager.state, ConnectionState.STREAMING)
        win.disconnect_all_hardware()
        self.assertEqual(win.state_manager.state, ConnectionState.IDLE)
        self.assertEqual(len(win.bounded_buffer), 0)

if __name__ == "__main__":
    unittest.main()
