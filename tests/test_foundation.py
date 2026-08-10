"""
Foundation Regression Tests for NeuroSim 2.0 (Phase 1)
Validates AppState, CentralStateManager, BoundedSignalBuffer, AcquisitionManager, and MainWindow decoupling.
"""

import unittest
from PySide6.QtWidgets import QApplication
from src.app.state import CentralStateManager, ConnectionState, InputSource
from src.processing.signal_buffer import BoundedSignalBuffer
from src.acquisition.acquisition_manager import AcquisitionManager
from src.ui.main_window import MainWindow

app = QApplication.instance() or QApplication([])

class TestFoundationArchitecture(unittest.TestCase):
    def setUp(self):
        self.state_mgr = CentralStateManager()
        self.buffer = BoundedSignalBuffer(capacity=10)
        self.acq_mgr = AcquisitionManager(self.state_mgr, self.buffer)

    def test_01_initial_state_is_idle(self):
        self.assertEqual(self.state_mgr.state, ConnectionState.IDLE)

    def test_02_initial_source_is_none(self):
        self.assertEqual(self.state_mgr.source, InputSource.NONE)

    def test_03_signal_buffer_initial_empty(self):
        self.assertEqual(len(self.buffer), 0)

    def test_04_no_simulator_activation_at_startup(self):
        win = MainWindow()
        self.assertEqual(win.state_manager.state, ConnectionState.IDLE)
        self.assertEqual(win.state_manager.source, InputSource.NONE)
        self.assertEqual(len(win.bounded_buffer), 0)

    def test_05_state_transition_idle_to_connecting(self):
        res = self.state_mgr.transition_to(ConnectionState.CONNECTING, "Connecting...")
        self.assertTrue(res)
        self.assertEqual(self.state_mgr.state, ConnectionState.CONNECTING)

    def test_06_state_transition_connecting_to_connected(self):
        self.state_mgr.transition_to(ConnectionState.CONNECTING)
        res = self.state_mgr.transition_to(ConnectionState.CONNECTED)
        self.assertTrue(res)
        self.assertEqual(self.state_mgr.state, ConnectionState.CONNECTED)

    def test_07_state_transition_connected_to_streaming(self):
        self.state_mgr.transition_to(ConnectionState.CONNECTING)
        self.state_mgr.transition_to(ConnectionState.CONNECTED)
        res = self.state_mgr.transition_to(ConnectionState.STREAMING)
        self.assertTrue(res)
        self.assertEqual(self.state_mgr.state, ConnectionState.STREAMING)

    def test_08_state_transition_streaming_to_idle(self):
        self.state_mgr.transition_to(ConnectionState.CONNECTING)
        self.state_mgr.transition_to(ConnectionState.CONNECTED)
        self.state_mgr.transition_to(ConnectionState.STREAMING)
        self.state_mgr.reset_to_idle()
        self.assertEqual(self.state_mgr.state, ConnectionState.IDLE)
        self.assertEqual(self.state_mgr.source, InputSource.NONE)

    def test_09_disconnect_clears_acquisition_and_buffer(self):
        self.acq_mgr.start_simulator()
        self.acq_mgr.generate_simulator_chunk(num_samples=5)
        self.assertEqual(len(self.buffer), 5)
        self.acq_mgr.stop_all()
        self.assertEqual(self.state_mgr.state, ConnectionState.IDLE)
        self.assertEqual(len(self.buffer), 0)

    def test_10_invalid_state_transitions_handled(self):
        # STREAMING to CONNECTING is invalid
        self.state_mgr.transition_to(ConnectionState.CONNECTING)
        self.state_mgr.transition_to(ConnectionState.CONNECTED)
        self.state_mgr.transition_to(ConnectionState.STREAMING)
        res = self.state_mgr.transition_to(ConnectionState.CONNECTING)
        self.assertFalse(res)
        self.assertEqual(self.state_mgr.state, ConnectionState.STREAMING)

    def test_11_buffer_append_works(self):
        self.buffer.append(12.5, source=InputSource.ESP32_USB)
        self.assertEqual(len(self.buffer), 1)
        self.assertEqual(self.buffer.get_samples()[0], 12.5)

    def test_12_buffer_clear_works(self):
        self.buffer.extend([1.0, 2.0, 3.0])
        self.assertEqual(len(self.buffer), 3)
        self.buffer.clear()
        self.assertEqual(len(self.buffer), 0)

    def test_13_buffer_capacity_is_enforced(self):
        buf = BoundedSignalBuffer(capacity=5)
        buf.extend([1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEqual(len(buf), 5)
        samples = buf.get_samples()
        self.assertEqual(list(samples), [4, 5, 6, 7, 8])

    def test_14_acquisition_normalized_sample_emission(self):
        received_samples = []
        self.acq_mgr.normalized_sample_received.connect(lambda val, meta: received_samples.append((val, meta)))
        self.acq_mgr.start_simulator()
        self.acq_mgr.generate_simulator_chunk(num_samples=3)
        self.assertEqual(len(received_samples), 3)
        self.assertEqual(received_samples[0][1]["source"], InputSource.SIMULATOR)

if __name__ == "__main__":
    unittest.main()
