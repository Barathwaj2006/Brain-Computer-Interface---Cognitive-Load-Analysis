"""
Unit Test Suite for Signal Quality & Acquisition Reliability Processing
Validates EEGQualityEvaluator flatline detection, saturation, artifact burden,
multichannel evaluation, and truthful impedance policy.
"""

import unittest
import numpy as np
from src.processing.quality import EEGQualityEvaluator

class TestSignalQualityEvaluator(unittest.TestCase):

    def setUp(self):
        self.evaluator = EEGQualityEvaluator(sampling_rate=250)

    def test_01_insufficient_samples(self):
        """Verify <32 samples returns insufficient data rating."""
        res = self.evaluator.evaluate_channel(np.array([1.0, 2.0, 3.0]))
        self.assertIsNone(res["quality_score"])
        self.assertEqual(res["rating"], "INSUFFICIENT DATA")
        self.assertFalse(res["valid"])

    def test_02_flatline_detection(self):
        """Verify constant zero signal triggers FLATLINE rating."""
        flat_signal = np.zeros(250)
        res = self.evaluator.evaluate_channel(flat_signal)
        self.assertEqual(res["quality_score"], 0.0)
        self.assertEqual(res["rating"], "FLATLINE")
        self.assertTrue(res["flatline"])
        self.assertFalse(res["valid"])

    def test_03_saturation_detection(self):
        """Verify high-amplitude clipped signal triggers SATURATED rating."""
        saturated_signal = np.full(250, 600.0)
        res = self.evaluator.evaluate_channel(saturated_signal)
        self.assertEqual(res["rating"], "SATURATED")
        self.assertTrue(res["saturation"])
        self.assertFalse(res["valid"])

    def test_04_clean_eeg_signal(self):
        """Verify clean sine wave signal triggers EXCELLENT quality score."""
        t = np.linspace(0, 1, 250)
        clean_signal = 10.0 * np.sin(2 * np.pi * 10 * t) # 10 Hz alpha wave, 10 uV
        res = self.evaluator.evaluate_channel(clean_signal)
        self.assertGreaterEqual(res["quality_score"], 80.0)
        self.assertIn(res["rating"], ("EXCELLENT", "GOOD"))
        self.assertTrue(res["valid"])

    def test_05_multichannel_evaluation_and_truthful_impedance(self):
        """Verify multi-channel evaluation and truthful impedance policy (no fake kΩ)."""
        t = np.linspace(0, 1, 250)
        ch_fp1 = 10.0 * np.sin(2 * np.pi * 10 * t)
        ch_fp2 = 12.0 * np.sin(2 * np.pi * 10 * t)
        ch_o1 = 8.0 * np.sin(2 * np.pi * 10 * t)
        ch_o2 = 9.0 * np.sin(2 * np.pi * 10 * t)

        all_samples = np.array([ch_fp1, ch_fp2, ch_o1, ch_o2])
        channels = ("FP1", "FP2", "O1", "O2")

        res = self.evaluator.evaluate_multichannel(all_samples, channels)
        self.assertIn("channels", res)
        self.assertIn("FP1", res["channels"])
        self.assertIn("O2", res["channels"])
        self.assertGreaterEqual(res["overall_score"], 80.0)
        self.assertTrue(res["valid"])

        # Enforce truthful impedance policy
        self.assertIn("impedance", res)
        self.assertFalse(res["impedance"]["available"])
        self.assertEqual(res["impedance"]["status"], "NOT_SUPPORTED")

if __name__ == "__main__":
    unittest.main()
