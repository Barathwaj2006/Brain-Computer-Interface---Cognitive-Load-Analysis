"""
Frequency & Power Spectral Density (PSD) Analysis Module
Calculates Welch PSD, absolute and relative band powers, dominant frequencies, and clinical stress indices.
"""

import numpy as np
from scipy import signal, integrate
from typing import Dict, Any, Tuple
from src.app.config import SAMPLING_RATE_HZ, BAND_LIMITS

class PSDAnalyzer:
    def __init__(self, sampling_rate: int = SAMPLING_RATE_HZ):
        self.sampling_rate = sampling_rate

    def compute_psd(self, eeg_signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute Welch Power Spectral Density (PSD).
        Returns:
            freqs (np.ndarray): Frequency array (Hz)
            psd (np.ndarray): Power Spectral Density array (uV^2/Hz)
        """
        nperseg = min(len(eeg_signal), self.sampling_rate * 2)
        if nperseg < 32:
            return np.array([]), np.array([])
            
        freqs, psd = signal.welch(eeg_signal, fs=self.sampling_rate, nperseg=nperseg, noverlap=nperseg//2)
        
        # Crop freqs to 0 - 45 Hz
        valid_idx = (freqs >= 0.5) & (freqs <= 45.0)
        return freqs[valid_idx], psd[valid_idx]

    def analyze_bands(self, freqs: np.ndarray, psd: np.ndarray) -> Dict[str, Any]:
        """
        Extract absolute and relative band powers, dominant band/frequency, and clinical stress ratios.
        """
        if len(freqs) == 0 or len(psd) == 0:
            return {
                'abs_powers': {'delta': 0.0, 'theta': 0.0, 'alpha': 0.0, 'beta': 0.0},
                'rel_powers': {'delta': 25.0, 'theta': 25.0, 'alpha': 25.0, 'beta': 25.0},
                'total_power': 0.0,
                'dominant_freq': 0.0,
                'dominant_band': 'ALPHA',
                'theta_beta_ratio': 1.0,
                'alpha_beta_ratio': 1.0,
                'stress_index': 0.5,
                'engagement_index': 0.5,
                'fatigue_metric': 0.5
            }

        dx = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
        abs_powers = {}

        for band, (low, high) in BAND_LIMITS.items():
            if band == 'gamma':
                continue
            idx = (freqs >= low) & (freqs <= high)
            if np.any(idx):
                # Simpson's / trapezoidal integration
                power = float(integrate.simpson(psd[idx], x=freqs[idx])) if hasattr(integrate, 'simpson') else float(np.trapz(psd[idx], dx=dx))
                abs_powers[band] = max(1e-6, power)
            else:
                abs_powers[band] = 1e-6

        total_power = sum(abs_powers.values())
        rel_powers = {band: (p / total_power) * 100.0 for band, p in abs_powers.items()}

        # Dominant frequency & band
        max_psd_idx = np.argmax(psd)
        dominant_freq = float(freqs[max_psd_idx])

        dominant_band = 'ALPHA'
        for band, (low, high) in BAND_LIMITS.items():
            if low <= dominant_freq <= high:
                dominant_band = band.upper()
                break

        # Clinical Stress Ratios
        theta_p = abs_powers['theta']
        alpha_p = abs_powers['alpha']
        beta_p  = abs_powers['beta']
        delta_p = abs_powers['delta']

        theta_beta_ratio = theta_p / max(1e-6, beta_p)  # Theta/Beta Ratio (TBR) -> Mental Fatigue
        alpha_beta_ratio = alpha_p / max(1e-6, beta_p)  # Relaxation vs Focus
        
        # Spectral Stress Index (SSI): ratio of Beta (high arousal) to (Alpha + Theta)
        stress_index = beta_p / max(1e-6, (alpha_p + theta_p))
        
        # Engagement Index: Beta / (Alpha + Theta)
        engagement_index = beta_p / max(1e-6, (alpha_p + theta_p))
        
        # Fatigue Metric: Theta / (Alpha + Beta)
        fatigue_metric = theta_p / max(1e-6, (alpha_p + beta_p))

        return {
            'abs_powers': abs_powers,
            'rel_powers': rel_powers,
            'total_power': total_power,
            'dominant_freq': dominant_freq,
            'dominant_band': dominant_band,
            'theta_beta_ratio': theta_beta_ratio,
            'alpha_beta_ratio': alpha_beta_ratio,
            'stress_index': stress_index,
            'engagement_index': engagement_index,
            'fatigue_metric': fatigue_metric
        }
