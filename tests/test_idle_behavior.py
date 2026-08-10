"""
Unit Tests for Zero-Input / IDLE State Behavior
Verifies that NeuroSim starts in IDLE/DISCONNECTED state without automatically
generating synthetic signal waveforms unless explicitly requested.
"""

import unittest
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

app = QApplication.instance() or QApplication([])

class TestIdleBehavior(unittest.TestCase):
    def test_default_idle_state_on_launch(self):
        win = MainWindow()
        self.assertEqual(win.active_hardware_source, "IDLE")
        self.assertEqual(len(win.signal_buffer), 0)

        # Trigger process_dsp_frame while IDLE
        win.process_dsp_frame()

        # Verify no synthetic samples were generated
        self.assertEqual(len(win.signal_buffer), 0)

    def test_explicit_simulator_start(self):
        win = MainWindow()
        self.assertEqual(win.active_hardware_source, "IDLE")

        # Explicitly start simulator mode
        win.start_simulator()
        self.assertEqual(win.active_hardware_source, "SIMULATOR")

        # Trigger process_dsp_frame while SIMULATOR
        win.process_dsp_frame()
        self.assertEqual(len(win.signal_buffer), 10)

    def test_disconnect_resets_to_idle(self):
        win = MainWindow()
        win.start_simulator()
        win.process_dsp_frame()
        self.assertGreater(len(win.signal_buffer), 0)

        # Disconnect hardware/simulator
        win.disconnect_all_hardware()
        self.assertEqual(win.active_hardware_source, "IDLE")
        self.assertEqual(len(win.signal_buffer), 0)

if __name__ == "__main__":
    unittest.main()
