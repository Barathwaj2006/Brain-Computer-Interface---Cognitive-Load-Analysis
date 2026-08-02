"""
Power Spectral Density (PSD) Analysis Module
Computes Welch PSD, relative band powers, clinical ratios, and validation metrics.
"""

import numpy as np
from scipy.signal import welch
import time
from src.app.config import SAMPLING_RATE, BANDS

class PSDAnalyzer:
    """
    Computes spectral band powers, Welch PSD estimation,
    clinical ratios, and validation tests.
    """

    def __init__(self, fs=SAMPLING_RATE):
        self.fs = fs

    def compute_psd(self, signal, nperseg=256):
        """
        Calculates Welch PSD for input time-series signal.
        Returns: (freqs, psd)
        """
        if len(signal) < nperseg:
            return np.array([0]), np.array([0])
        
        freqs, psd = welch(signal, fs=self.fs, nperseg=min(nperseg, len(signal)))
        return freqs, psd

    def extract_band_powers(self, freqs, psd):
        """
        Integrates PSD across Delta, Theta, Alpha, and Beta frequency bands.
        Returns dictionary of absolute and relative band powers.
        """
        band_powers = {}
        total_power = np.sum(psd) + 1e-12

        for band_name, (f_min, f_max) in BANDS.items():
            idx = np.where((freqs >= f_min) & (freqs <= f_max))[0]
            if len(idx) > 0:
                abs_power = np.trapz(psd[idx], freqs[idx])
            else:
                abs_power = 0.0
            band_powers[f"{band_name}_abs"] = float(abs_power)

        abs_total = sum(band_powers.values()) + 1e-12
        for band_name in BANDS.keys():
            band_powers[f"{band_name}_rel"] = float(band_powers[f"{band_name}_abs"] / abs_total) * 100.0

        return band_powers

    def compute_metrics(self, band_powers, freqs=None, psd=None):
        """
        Computes clinical stress index, TBR, engagement, dominant frequency,
        and telemetry latency metrics.
        """
        start_t = time.perf_counter()

        delta = band_powers.get('delta_rel', 25.0)
        theta = band_powers.get('theta_rel', 25.0)
        alpha = band_powers.get('alpha_rel', 25.0)
        beta = band_powers.get('beta_rel', 25.0)

        # Ratios
        stress_index = beta / (alpha + theta + 1e-6)
        tbr = theta / (beta + 1e-6)
        abr = alpha / (beta + 1e-6)
        engagement = beta / (alpha + theta + 1e-6)
        fatigue = theta / (alpha + beta + 1e-6)

        # Dominant Frequency
        dom_freq = 10.0
        dom_band = "ALPHA"
        if freqs is not None and psd is not None and len(psd) > 0:
            dom_idx = np.argmax(psd)
            dom_freq = float(freqs[dom_idx])
            if dom_freq <= 4.0:
                dom_band = "DELTA"
            elif dom_freq <= 8.0:
                dom_band = "THETA"
            elif dom_freq <= 13.0:
                dom_band = "ALPHA"
            else:
                dom_band = "BETA"

        calc_latency = (time.perf_counter() - start_t) * 1000.0

        return {
            'stress_index': float(stress_index),
            'tbr': float(tbr),
            'abr': float(abr),
            'engagement': float(engagement),
            'fatigue': float(fatigue),
            'dominant_frequency': float(dom_freq),
            'dominant_band': dom_band,
            'calc_latency_ms': float(calc_latency)
        }

    def run_validation_test(self, test_band):
        """
        Runs automated DSP validation self-test for a specified band.
        Generates synthetic pure test tone, computes detected peak frequency,
        verifies band match, and returns accuracy PASS/FAIL metrics.
        """
        test_freqs = {
            'delta': 2.0,
            'theta': 6.0,
            'alpha': 10.0,
            'beta': 20.0
        }
        
        target_f = test_freqs.get(test_band.lower(), 10.0)
        t = np.linspace(0, 5, self.fs * 5)
        # Pure tone + small noise
        test_signal = np.sin(2 * np.pi * target_f * t) + np.random.normal(0, 0.05, len(t))

        freqs, psd = self.compute_psd(test_signal, nperseg=512)
        bands = self.extract_band_powers(freqs, psd)
        metrics = self.compute_metrics(bands, freqs, psd)

        detected_f = metrics['dominant_frequency']
        detected_band = metrics['dominant_band']
        freq_error = abs(detected_f - target_f)
        
        passed = (freq_error <= 0.5) and (detected_band.lower() == test_band.lower())

        return {
            'test_band': test_band.upper(),
            'target_frequency_hz': target_f,
            'detected_frequency_hz': detected_f,
            'detected_band': detected_band,
            'frequency_error_hz': round(freq_error, 2),
            'result': "PASS" if passed else "FAIL",
            'passed': passed
        }
