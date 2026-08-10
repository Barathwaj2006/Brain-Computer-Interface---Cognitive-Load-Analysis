"""
Phase 1C Signal Acquisition Core Test Suite for NeuroSim 2.0
Validates SyntheticSignalSource generation, multi-channel alignment, BoundedSignalBuffer capacity & FIFO eviction,
AcquisitionManager lifecycle orchestration, and end-to-end signal ingestion.
"""

import unittest
import time
import numpy as np
from PySide6.QtWidgets import QApplication

from src.core.enums import SignalSourceType
from src.core.signal_contract import SignalFrame
from src.processing.signal_buffer import BoundedSignalBuffer, SignalBuffer
from src.acquisition.base_acquirer import BaseSignalSource
from src.acquisition.synthetic_source import SyntheticSignalSource
from src.acquisition.acquisition_manager import AcquisitionManager

app = QApplication.instance() or QApplication([])

class TestPhase1CAcquisitionCore(unittest.TestCase):

    def setUp(self):
        self.buffer = BoundedSignalBuffer(capacity=1250, sampling_rate=250, channels=("Ch1",))
        self.acq_mgr = AcquisitionManager(self.buffer)
        self.syn_source = SyntheticSignalSource(sampling_rate=250, channels=("Ch1",), seed=42)
        self.acq_mgr.register_source("synthetic", self.syn_source)

    def test_01_source_creation(self):
        """1. Source creation."""
        syn = SyntheticSignalSource(sampling_rate=250, channels=("Ch1",))
        self.assertEqual(syn.source_type, SignalSourceType.SIMULATOR)
        self.assertEqual(syn.source_name, "SyntheticSource")
        self.assertEqual(syn.sampling_rate, 250)
        self.assertEqual(syn.status(), "IDLE")

    def test_02_250hz_generation(self):
        """2. 250 Hz generation."""
        syn = SyntheticSignalSource(sampling_rate=250, seed=100)
        frame = syn.generate_frame(num_samples=250)
        self.assertEqual(frame.sampling_rate, 250)
        self.assertEqual(frame.num_samples, 250)

    def test_03_correct_sample_count(self):
        """3. Correct sample count."""
        frame = self.syn_source.generate_frame(num_samples=50)
        self.assertEqual(len(frame.data[0]), 50)
        self.assertEqual(frame.num_samples, 50)

    def test_04_deterministic_generation(self):
        """4. Deterministic generation with random seed."""
        syn1 = SyntheticSignalSource(sampling_rate=250, seed=777)
        f1 = syn1.generate_frame(num_samples=100)

        syn2 = SyntheticSignalSource(sampling_rate=250, seed=777)
        f2 = syn2.generate_frame(num_samples=100)

        self.assertTrue(np.allclose(f1.data, f2.data))

    def test_05_start_stop_behavior(self):
        """5. Start/stop behavior."""
        self.acq_mgr.select_source("synthetic")
        self.assertTrue(self.acq_mgr.start())
        self.assertEqual(self.acq_mgr.status(), "STREAMING")

        self.assertTrue(self.acq_mgr.stop())
        self.assertEqual(self.acq_mgr.status(), "IDLE")

    def test_06_rolling_buffer_append(self):
        """6. Rolling buffer append."""
        frame = self.syn_source.generate_frame(num_samples=20)
        self.buffer.append_frame(frame)
        self.assertEqual(len(self.buffer), 20)
        self.assertEqual(len(self.buffer.get_samples(0)), 20)

    def test_07_rolling_buffer_capacity(self):
        """7. Rolling buffer capacity capping."""
        buf = BoundedSignalBuffer(capacity=100, sampling_rate=250)
        for i in range(15): # 15 frames of 10 samples = 150 samples total
            frame = SignalFrame(
                timestamp=1.0 + i*0.04, sequence=i*10, sampling_rate=250,
                channel_count=1, channels=("Ch1",), data=([float(x) for x in range(10)],)
            )
            buf.append_frame(frame)
        self.assertEqual(len(buf), 100)
        self.assertEqual(buf.capacity, 100)

    def test_08_fifo_eviction(self):
        """8. FIFO eviction when capacity is exceeded."""
        buf = BoundedSignalBuffer(capacity=5, sampling_rate=250)
        frame1 = SignalFrame(timestamp=1.0, sequence=0, sampling_rate=250, channel_count=1, channels=("Ch1",), data=([1.0, 2.0, 3.0],))
        frame2 = SignalFrame(timestamp=2.0, sequence=3, sampling_rate=250, channel_count=1, channels=("Ch1",), data=([4.0, 5.0, 6.0],))
        
        buf.append_frame(frame1)
        buf.append_frame(frame2)

        self.assertEqual(len(buf), 5)
        samples = buf.get_samples(0)
        seqs = buf.get_sequences()
        self.assertEqual(list(samples), [2.0, 3.0, 4.0, 5.0, 6.0])
        self.assertEqual(list(seqs), [1, 2, 3, 4, 5])

    def test_09_chronological_ordering(self):
        """9. Chronological ordering preservation."""
        buf = BoundedSignalBuffer(capacity=50, sampling_rate=250)
        for i in range(5):
            frame = SignalFrame(
                timestamp=10.0 + i * 0.1, sequence=i * 5, sampling_rate=250,
                channel_count=1, channels=("Ch1",), data=([float(i)] * 5,)
            )
            buf.append_frame(frame)
        
        ts = buf.get_timestamps()
        self.assertTrue(all(ts[k] <= ts[k+1] for k in range(len(ts)-1)))

    def test_10_clear(self):
        """10. Clear behavior."""
        frame = self.syn_source.generate_frame(num_samples=30)
        self.buffer.append_frame(frame)
        self.assertEqual(len(self.buffer), 30)
        self.buffer.clear()
        self.assertEqual(len(self.buffer), 0)
        self.assertEqual(self.buffer.duration_sec, 0.0)

    def test_11_empty_buffer_behavior(self):
        """11. Empty buffer behavior."""
        buf = BoundedSignalBuffer(capacity=100)
        self.assertEqual(len(buf), 0)
        self.assertEqual(len(buf.get_samples(0)), 0)
        self.assertEqual(len(buf.get_all_samples()[0]), 0)
        self.assertIsNone(buf.latest_timestamp)
        self.assertEqual(buf.duration_sec, 0.0)

    def test_12_multi_channel_alignment(self):
        """12. Multi-channel EEG temporal alignment."""
        mc_syn = SyntheticSignalSource(sampling_rate=250, channels=("F3", "F4", "C3", "C4"), seed=123)
        mc_buf = BoundedSignalBuffer(capacity=500, sampling_rate=250, channels=("F3", "F4", "C3", "C4"))
        
        frame = mc_syn.generate_frame(num_samples=20)
        mc_buf.append_frame(frame)

        self.assertEqual(mc_buf.channel_count, 4)
        self.assertEqual(mc_buf.channels, ("F3", "F4", "C3", "C4"))
        all_s = mc_buf.get_all_samples()
        self.assertEqual(all_s.shape, (4, 20))

    def test_13_canonical_signal_frame_compatibility(self):
        """13. Canonical SignalFrame compatibility."""
        frame = SignalFrame(
            timestamp=100.0, sequence=5, sampling_rate=250, channel_count=1, channels=("Ch1",),
            data=([1.0, 2.0, 3.0],), source=SignalSourceType.SIMULATOR
        )
        self.buffer.append_frame(frame)
        self.assertEqual(len(self.buffer), 3)

    def test_14_acquisition_lifecycle(self):
        """14. Acquisition lifecycle states."""
        self.acq_mgr.select_source("synthetic")
        self.assertEqual(self.acq_mgr.status(), "IDLE")

        self.acq_mgr.start()
        self.assertEqual(self.acq_mgr.status(), "STREAMING")

        self.acq_mgr.pause()
        self.assertEqual(self.acq_mgr.status(), "PAUSED")

        self.acq_mgr.resume()
        self.assertEqual(self.acq_mgr.status(), "STREAMING")

        self.acq_mgr.stop()
        self.assertEqual(self.acq_mgr.status(), "IDLE")

    def test_15_invalid_input_handling(self):
        """15. Invalid input handling."""
        with self.assertRaises(TypeError):
            self.buffer.append_frame("not_a_frame")

        with self.assertRaises(IndexError):
            self.buffer.get_samples(channel_idx=99)

    def test_16_end_to_end_integration(self):
        """16. End-to-end integration test: Source -> Frame -> Manager -> Buffer -> Snapshot."""
        mc_syn = SyntheticSignalSource(sampling_rate=250, channels=("F3", "F4"), seed=555)
        mc_buf = BoundedSignalBuffer(capacity=1250, sampling_rate=250, channels=("F3", "F4"))
        mgr = AcquisitionManager(mc_buf)
        mgr.register_source("e2e_syn", mc_syn)
        mgr.select_source("e2e_syn")

        # Manually generate 5 frames of 50 samples = 250 samples (1.0s @ 250 Hz)
        for i in range(5):
            f = mc_syn.generate_frame(num_samples=50)
            mgr._process_incoming_frame(f)

        snap = mc_buf.snapshot()
        self.assertEqual(snap["count"], 250)
        self.assertEqual(snap["channel_count"], 2)
        self.assertEqual(snap["channels"], ("F3", "F4"))
        self.assertEqual(snap["sampling_rate"], 250)
        self.assertEqual(snap["all_samples"].shape, (2, 250))
        self.assertAlmostEqual(snap["duration_sec"], 1.0, places=2)
        self.assertIsNotNone(snap["latest_timestamp"])
        self.assertIn("sequences", snap)
        self.assertEqual(len(snap["sequences"]), 250)

if __name__ == "__main__":
    unittest.main()
