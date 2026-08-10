"""
Phase 2 Signal Buffer & Acquisition Core Test Suite for NeuroSim 2.0
Validates SignalFrame validation, BaseSignalSource interface, BoundedSignalBuffer capacity & FIFO eviction,
SyntheticSignalSource generation, and AcquisitionManager orchestration.
"""

import unittest
import time
import numpy as np
from PySide6.QtWidgets import QApplication

from src.app.state import CentralStateManager, ConnectionState, InputSource
from src.processing.signal_buffer import BoundedSignalBuffer, SignalBuffer
from src.acquisition.contracts import SignalFrame, BaseSignalSource, NormalizedFrame
from src.acquisition.synthetic_source import SyntheticSignalSource
from src.acquisition.acquisition_manager import AcquisitionManager

app = QApplication.instance() or QApplication([])

class TestPhase2AcquisitionCore(unittest.TestCase):
    def setUp(self):
        self.state_mgr = CentralStateManager()
        self.buffer = BoundedSignalBuffer(capacity=1250, sampling_rate=250)
        self.acq_mgr = AcquisitionManager(self.state_mgr, self.buffer)

    def test_01_signal_frame_creation(self):
        """1. SignalFrame creation with valid parameters."""
        frame = SignalFrame(
            timestamp=1000.0,
            sequence=42,
            sampling_rate=250,
            channel_count=1,
            channels=["Ch1"],
            data=[1.5, 2.5, 3.5],
            source=InputSource.SIMULATOR,
            metadata={"test": "valid"}
        )
        self.assertEqual(frame.timestamp, 1000.0)
        self.assertEqual(frame.sequence, 42)
        self.assertEqual(frame.sampling_rate, 250)
        self.assertEqual(len(frame.data), 3)

    def test_02_invalid_signal_frame_rejection(self):
        """2. Invalid SignalFrame rejection."""
        # Invalid sampling rate
        with self.assertRaises(ValueError):
            SignalFrame(sampling_rate=-10)

        # Invalid sequence
        with self.assertRaises(ValueError):
            SignalFrame(sequence=-1)

        # None data
        with self.assertRaises(ValueError):
            SignalFrame(data=None)

        # Malformed data string
        with self.assertRaises(ValueError):
            SignalFrame(data=["invalid_number"])

    def test_03_signal_source_interface_lifecycle(self):
        """3. Generic SignalSource interface lifecycle methods."""
        class DummySource(BaseSignalSource):
            def start(self):
                self._running = True
                return True
            def stop(self):
                self._running = False
                self._paused = False
                return True
            def pause(self):
                self._paused = True
                return True
            def resume(self):
                self._paused = False
                return True

        src = DummySource("Dummy")
        self.assertFalse(src.is_running())
        self.assertFalse(src.is_paused())

        src.start()
        self.assertTrue(src.is_running())

        src.pause()
        self.assertTrue(src.is_paused())

        src.resume()
        self.assertFalse(src.is_paused())

        src.stop()
        self.assertFalse(src.is_running())

    def test_04_synthetic_source_startup(self):
        """4. Synthetic source startup."""
        syn = SyntheticSignalSource(sampling_rate=250)
        res = syn.start()
        self.assertTrue(res)
        self.assertTrue(syn.is_running())
        syn.stop()

    def test_05_synthetic_source_stopping(self):
        """5. Synthetic source stopping."""
        syn = SyntheticSignalSource(sampling_rate=250)
        syn.start()
        syn.stop()
        self.assertFalse(syn.is_running())

    def test_06_pause_resume_behavior(self):
        """6. Pause/resume behavior."""
        syn = SyntheticSignalSource(sampling_rate=250)
        syn.start()
        syn.pause()
        self.assertTrue(syn.is_paused())
        syn.resume()
        self.assertFalse(syn.is_paused())
        syn.stop()

    def test_07_sequence_progression(self):
        """7. Sequence progression is monotonically increasing."""
        syn = SyntheticSignalSource(sampling_rate=250)
        f1 = syn.generate_frame(num_samples=10)
        f2 = syn.generate_frame(num_samples=10)
        self.assertEqual(f1.sequence, 0)
        self.assertEqual(f2.sequence, 10)

    def test_08_timestamp_progression(self):
        """8. Timestamp progression."""
        syn = SyntheticSignalSource(sampling_rate=250)
        f1 = syn.generate_frame(num_samples=10)
        time.sleep(0.01)
        f2 = syn.generate_frame(num_samples=10)
        self.assertGreaterEqual(f2.timestamp, f1.timestamp)

    def test_09_250hz_configuration(self):
        """9. 250 Hz configuration."""
        self.assertEqual(self.buffer.sampling_rate, 250)

    def test_10_rolling_buffer_capacity(self):
        """10. Rolling buffer capacity = 1250."""
        self.assertEqual(self.buffer.capacity, 1250)

    def test_11_fifo_eviction(self):
        """11. FIFO eviction when capacity is exceeded."""
        buf = BoundedSignalBuffer(capacity=5)
        for i in range(10):
            buf.append(float(i), sequence=i)
        
        self.assertEqual(len(buf), 5)
        samples = buf.get_samples()
        seqs = buf.get_sequences()
        self.assertEqual(list(samples), [5.0, 6.0, 7.0, 8.0, 9.0])
        self.assertEqual(list(seqs), [5, 6, 7, 8, 9])

    def test_12_buffer_clearing(self):
        """12. Buffer clearing."""
        self.buffer.extend([1.0, 2.0, 3.0])
        self.assertEqual(len(self.buffer), 3)
        self.buffer.clear()
        self.assertEqual(len(self.buffer), 0)

    def test_13_acquisition_manager_source_registration(self):
        """13. AcquisitionManager source registration."""
        syn = SyntheticSignalSource(sampling_rate=250)
        self.acq_mgr.register_source("custom_syn", syn)
        res = self.acq_mgr.select_source("custom_syn")
        self.assertTrue(res)
        self.assertEqual(self.acq_mgr.active_source, syn)

    def test_14_acquisition_manager_start_stop(self):
        """14. AcquisitionManager start/stop."""
        self.acq_mgr.select_source("synthetic")
        self.acq_mgr.start()
        self.assertEqual(self.state_mgr.state, ConnectionState.STREAMING)
        self.acq_mgr.stop()
        self.assertEqual(self.state_mgr.state, ConnectionState.IDLE)

    def test_15_acquisition_manager_buffer_delivery(self):
        """15. AcquisitionManager -> buffer delivery."""
        self.acq_mgr.start_simulator()
        self.acq_mgr.generate_simulator_chunk(num_samples=25)
        self.assertEqual(len(self.buffer), 25)

    def test_16_no_data_after_stop(self):
        """16. No data after stop."""
        self.acq_mgr.start_simulator()
        self.acq_mgr.generate_simulator_chunk(num_samples=10)
        self.assertEqual(len(self.buffer), 10)
        
        self.acq_mgr.stop_all()
        self.assertEqual(len(self.buffer), 0)
        
        # Generation after stop produces 0 new buffer items
        self.acq_mgr.generate_simulator_chunk(num_samples=10)
        self.assertEqual(len(self.buffer), 0)

    def test_17_no_uncontrolled_buffer_growth(self):
        """17. No uncontrolled buffer growth beyond 1250."""
        self.acq_mgr.start_simulator()
        for _ in range(150):
            self.acq_mgr.generate_simulator_chunk(num_samples=10) # 1500 samples total
        self.assertEqual(len(self.buffer), 1250)

    def test_18_deterministic_seeded_generation(self):
        """18. Deterministic seeded generation."""
        syn1 = SyntheticSignalSource(sampling_rate=250, seed=999)
        f1 = syn1.generate_frame(num_samples=50)

        syn2 = SyntheticSignalSource(sampling_rate=250, seed=999)
        f2 = syn2.generate_frame(num_samples=50)

        self.assertTrue(np.allclose(f1.data, f2.data))

if __name__ == "__main__":
    unittest.main()
