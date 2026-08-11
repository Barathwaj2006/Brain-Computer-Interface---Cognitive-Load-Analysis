"""
Phase 1D Core Pipeline Integration Test Suite for NeuroSim 2.0
Validates end-to-end integration across:
SyntheticSignalSource -> SignalFrame -> AcquisitionManager -> BoundedSignalBuffer -> PSDAnalyzer -> Quantitative Results
Includes numerical frequency validations for Delta (2Hz), Alpha (10Hz), Beta (20Hz), and Mixed signals,
multi-channel alignment, FIFO buffer eviction, and boundary error handling.
"""

import unittest
import time
import numpy as np

from src.core.enums import SignalSourceType
from src.core.signal_contract import SignalFrame
from src.processing.signal_buffer import BoundedSignalBuffer, SignalBuffer
from src.acquisition.synthetic_source import SyntheticSignalSource
from src.acquisition.acquisition_manager import AcquisitionManager
from src.processing.psd import PSDAnalyzer
from src.features.extractor import EEGFeatureExtractor

class TestPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.buffer = BoundedSignalBuffer(capacity=1250, sampling_rate=250, channels=("Ch1",))
        self.acq_mgr = AcquisitionManager(self.buffer)
        self.psd_analyzer = PSDAnalyzer(sampling_rate=250)

    def test_01_end_to_end_pipeline_flow(self):
        """1. Complete end-to-end flow: Source -> Frame -> Manager -> Buffer -> Snapshot -> PSD -> Metrics."""
        syn = SyntheticSignalSource(sampling_rate=250, channels=("Ch1",), seed=42)
        syn.set_noise(0.01)
        self.acq_mgr.register_source("syn", syn)
        self.acq_mgr.select_source("syn")

        # Ingest 10 frames of 25 samples = 250 samples (1 second of data @ 250 Hz)
        for _ in range(10):
            frame = syn.generate_frame(num_samples=25)
            self.acq_mgr._process_incoming_frame(frame)

        # 1. Take snapshot
        snap = self.buffer.snapshot()
        self.assertEqual(snap["count"], 250)
        self.assertEqual(snap["sampling_rate"], 250)

        # 2. Compute PSD on snapshot samples
        freqs, psd = self.psd_analyzer.compute_psd(snap["samples"])
        self.assertGreater(len(freqs), 1)
        self.assertGreater(len(psd), 1)

        # 3. Extract band powers & clinical metrics
        combined_metrics = self.psd_analyzer.analyze_bands(freqs, psd)

        self.assertIn("tbr", combined_metrics)
        self.assertIn("abr", combined_metrics)
        self.assertIn("dominant_frequency", combined_metrics)
        self.assertIn("dominant_band", combined_metrics)

        # 4. Extract feature vector
        psd_metrics_for_extractor = {
            'rel_powers': {
                'delta': combined_metrics.get('delta_rel', 0.0),
                'theta': combined_metrics.get('theta_rel', 0.0),
                'alpha': combined_metrics.get('alpha_rel', 0.0),
                'beta': combined_metrics.get('beta_rel', 0.0),
            },
            'theta_beta_ratio': combined_metrics.get('tbr', 1.0),
            'alpha_beta_ratio': combined_metrics.get('abr', 1.0),
            'stress_index': combined_metrics.get('stress_index', 0.5),
            'total_power': np.sum(psd)
        }
        features = EEGFeatureExtractor.extract_features(psd_metrics_for_extractor)
        self.assertEqual(len(features), 8)

    def test_02_pure_delta_numerical_validation(self):
        """2. Pure Delta signal validation (dominant freq ~ 2 Hz, Delta rel power dominates)."""
        syn = SyntheticSignalSource(sampling_rate=250, channels=("Ch1",), seed=101)
        syn.set_amplitudes(delta=1.0, theta=0.0, alpha=0.0, beta=0.0)
        syn.set_noise(0.0)  # Pure tone

        buf = BoundedSignalBuffer(capacity=1250, sampling_rate=250)
        for _ in range(25): # 2500 samples = 10s @ 250 Hz
            frame = syn.generate_frame(num_samples=100)
            buf.append_frame(frame)

        snap = buf.snapshot()
        freqs, psd = self.psd_analyzer.compute_psd(snap["samples"], nperseg=512)
        metrics = self.psd_analyzer.analyze_bands(freqs, psd)

        # Dominant frequency around 2.0 Hz
        self.assertAlmostEqual(metrics["dominant_frequency"], 2.0, delta=1.0)
        self.assertEqual(metrics["dominant_band"], "DELTA")

        # Delta relative power dominates (> 70%)
        self.assertGreater(metrics["delta_rel"], 70.0)

    def test_03_pure_alpha_numerical_validation(self):
        """3. Pure Alpha signal validation (dominant freq ~ 10 Hz, Alpha rel power dominates)."""
        syn = SyntheticSignalSource(sampling_rate=250, channels=("Ch1",), seed=202)
        syn.set_amplitudes(delta=0.0, theta=0.0, alpha=1.0, beta=0.0)
        syn.set_noise(0.0)

        buf = BoundedSignalBuffer(capacity=1250, sampling_rate=250)
        for _ in range(25):
            frame = syn.generate_frame(num_samples=100)
            buf.append_frame(frame)

        snap = buf.snapshot()
        freqs, psd = self.psd_analyzer.compute_psd(snap["samples"], nperseg=512)
        metrics = self.psd_analyzer.analyze_bands(freqs, psd)

        # Dominant frequency around 10.0 Hz
        self.assertAlmostEqual(metrics["dominant_frequency"], 10.0, delta=1.0)
        self.assertEqual(metrics["dominant_band"], "ALPHA")

        # Alpha relative power dominates (> 70%)
        self.assertGreater(metrics["alpha_rel"], 70.0)

    def test_04_pure_beta_numerical_validation(self):
        """4. Pure Beta signal validation (dominant freq ~ 20 Hz, Beta rel power dominates)."""
        syn = SyntheticSignalSource(sampling_rate=250, channels=("Ch1",), seed=303)
        syn.set_amplitudes(delta=0.0, theta=0.0, alpha=0.0, beta=1.0)
        syn.set_noise(0.0)

        buf = BoundedSignalBuffer(capacity=1250, sampling_rate=250)
        for _ in range(25):
            frame = syn.generate_frame(num_samples=100)
            buf.append_frame(frame)

        snap = buf.snapshot()
        freqs, psd = self.psd_analyzer.compute_psd(snap["samples"], nperseg=512)
        metrics = self.psd_analyzer.analyze_bands(freqs, psd)

        # Dominant frequency around 20.0 Hz
        self.assertAlmostEqual(metrics["dominant_frequency"], 20.0, delta=1.0)
        self.assertEqual(metrics["dominant_band"], "BETA")

        # Beta relative power dominates (> 70%)
        self.assertGreater(metrics["beta_rel"], 70.0)

    def test_05_mixed_eeg_signal_validation(self):
        """5. Mixed EEG signal validation (Delta + Theta + Alpha + Beta)."""
        syn = SyntheticSignalSource(sampling_rate=250, channels=("Ch1",), seed=404)
        syn.set_amplitudes(delta=0.3, theta=0.4, alpha=0.8, beta=0.3)
        syn.set_noise(0.05)

        buf = BoundedSignalBuffer(capacity=1250, sampling_rate=250)
        for _ in range(25):
            frame = syn.generate_frame(num_samples=100)
            buf.append_frame(frame)

        snap = buf.snapshot()
        freqs, psd = self.psd_analyzer.compute_psd(snap["samples"], nperseg=512)
        metrics = self.psd_analyzer.analyze_bands(freqs, psd)

        # Total power > 0
        total_power = float(np.sum(psd))
        self.assertGreater(total_power, 0.0)

        # Sum of relative powers ~ 100%
        rel_sum = metrics["delta_rel"] + metrics["theta_rel"] + metrics["alpha_rel"] + metrics["beta_rel"]
        self.assertAlmostEqual(rel_sum, 100.0, delta=0.5)

        # TBR & ABR clinical ratios are positive finite floats
        self.assertGreater(metrics["tbr"], 0.0)
        self.assertGreater(metrics["abr"], 0.0)
        self.assertFalse(np.isnan(metrics["tbr"]))
        self.assertFalse(np.isinf(metrics["tbr"]))

    def test_06_buffer_capacity_fifo_eviction_immutability(self):
        """6. Buffer 1250 capacity, FIFO eviction, and canonical frame immutability."""
        buf = BoundedSignalBuffer(capacity=1250, sampling_rate=250)
        syn = SyntheticSignalSource(sampling_rate=250, seed=505)

        # Ingest 1500 samples (15 frames x 100 samples)
        for _ in range(15):
            frame = syn.generate_frame(num_samples=100)
            # Immutability check: modifying frame raises error
            with self.assertRaises(Exception):
                frame.sequence = 999
            buf.append_frame(frame)

        # Buffer capped at 1250
        self.assertEqual(len(buf), 1250)

        # Snapshot stability check
        snap1 = buf.snapshot()
        snap2 = buf.snapshot()
        self.assertTrue(np.array_equal(snap1["samples"], snap2["samples"]))
        self.assertEqual(snap1["count"], 1250)

    def test_07_multi_channel_alignment_and_analysis(self):
        """7. Multi-channel EEG alignment (F3, F4, C3, C4) and per-channel analysis."""
        mc_channels = ("F3", "F4", "C3", "C4")
        syn = SyntheticSignalSource(sampling_rate=250, channels=mc_channels, seed=606)
        buf = BoundedSignalBuffer(capacity=1250, sampling_rate=250, channels=mc_channels)

        for _ in range(10):
            frame = syn.generate_frame(num_samples=50)
            buf.append_frame(frame)

        snap = buf.snapshot()
        self.assertEqual(snap["channel_count"], 4)
        self.assertEqual(snap["channels"], mc_channels)
        self.assertEqual(snap["all_samples"].shape, (4, 500))

        # Compute PSD per channel independently
        per_ch_metrics = []
        for ch_idx in range(4):
            ch_samples = snap["all_samples"][ch_idx]
            freqs, psd = self.psd_analyzer.compute_psd(ch_samples)
            m = self.psd_analyzer.analyze_bands(freqs, psd)
            per_ch_metrics.append(m)

        self.assertEqual(len(per_ch_metrics), 4)
        for m in per_ch_metrics:
            self.assertIn("dominant_frequency", m)

    def test_08_error_and_boundary_handling(self):
        """8. Rejection of empty/insufficient buffer data."""
        empty_buf = BoundedSignalBuffer(capacity=1250, sampling_rate=250)
        snap = empty_buf.snapshot()
        self.assertEqual(snap["count"], 0)

        # PSDAnalyzer on empty data (< 32 samples) returns 0 arrays gracefully
        freqs, psd = self.psd_analyzer.compute_psd(snap["samples"])
        self.assertEqual(list(freqs), [0.0])
        self.assertEqual(list(psd), [0.0])

if __name__ == "__main__":
    unittest.main()
