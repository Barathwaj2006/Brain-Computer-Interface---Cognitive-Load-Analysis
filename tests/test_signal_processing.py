"""
Unit Tests — Signal Processing Engine & PSD Analysis
Verifies spectral accuracy for pure synthetic frequencies:
- 2 Hz -> DELTA dominant
- 6 Hz -> THETA dominant
- 10 Hz -> ALPHA dominant
- 20 Hz -> BETA dominant
"""

import unittest
import numpy as np
from src.simulation.eeg_generator import SyntheticEEGGenerator
from src.processing.filter import EEGFilter
from src.processing.psd import PSDAnalyzer

class TestSignalProcessing(unittest.TestCase):
    def setUp(self):
        self.generator = SyntheticEEGGenerator(sampling_rate=250)
        self.filter_obj = EEGFilter(sampling_rate=250)
        self.psd_analyzer = PSDAnalyzer(sampling_rate=250)

    def _test_pure_band(self, delta, theta, alpha, beta, expected_band):
        self.generator.set_amplitudes(delta, theta, alpha, beta)
        self.generator.set_noise(0.01) # Low noise for pure test

        waveform, _ = self.generator.generate_chunk(1250) # 5 sec
        filtered = self.filter_obj.process(waveform)
        freqs, psd = self.psd_analyzer.compute_psd(filtered)
        metrics = self.psd_analyzer.analyze_bands(freqs, psd)

        detected = metrics['dominant_band']
        self.assertEqual(detected, expected_band, f"Expected {expected_band}, detected {detected}")

    def test_delta_dominance(self):
        self._test_pure_band(1.0, 0.05, 0.05, 0.05, 'DELTA')

    def test_theta_dominance(self):
        self._test_pure_band(0.05, 1.0, 0.05, 0.05, 'THETA')

    def test_alpha_dominance(self):
        self._test_pure_band(0.05, 0.05, 1.0, 0.05, 'ALPHA')

    def test_beta_dominance(self):
        self._test_pure_band(0.05, 0.05, 0.05, 1.0, 'BETA')

if __name__ == '__main__':
    unittest.main()
