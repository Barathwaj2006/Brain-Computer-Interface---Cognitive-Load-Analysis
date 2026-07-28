"""
Synthetic EEG Signal Generator Module
Generates real-time EEG-like waveforms combining Delta (2Hz), Theta (6Hz), Alpha (10Hz), and Beta (20Hz)
components based on potentiometer simulation controls.
"""

import time
import numpy as np
from typing import Tuple, Dict
from src.app.config import SAMPLING_RATE_HZ, FREQ_TARGETS

class SyntheticEEGGenerator:
    def __init__(self, sampling_rate: int = SAMPLING_RATE_HZ):
        self.sampling_rate = sampling_rate
        # Default amplitudes (0.0 to 1.0)
        self.amplitudes = {
            'delta': 0.3,
            'theta': 0.4,
            'alpha': 0.8,
            'beta': 0.3
        }
        self.noise_level = 0.1
        self.t_cursor = 0.0
        # Phase tracking to prevent phase jumps when slider changes
        self.phases = {
            'delta': 0.0,
            'theta': 0.0,
            'alpha': 0.0,
            'beta': 0.0
        }

    def set_amplitudes(self, delta: float, theta: float, alpha: float, beta: float):
        """Update amplitudes (0.0 to 1.0) dynamically."""
        self.amplitudes['delta'] = max(0.0, min(1.0, float(delta)))
        self.amplitudes['theta'] = max(0.0, min(1.0, float(theta)))
        self.amplitudes['alpha'] = max(0.0, min(1.0, float(alpha)))
        self.amplitudes['beta'] = max(0.0, min(1.0, float(beta)))

    def set_noise(self, noise_level: float):
        """Update gaussian noise standard deviation."""
        self.noise_level = max(0.0, min(1.0, float(noise_level)))

    def generate_chunk(self, num_samples: int) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Generate num_samples of synthetic EEG waveform.
        Returns:
            samples (np.ndarray): combined waveform voltage values in uV range (~ -100 to +100 uV)
            current_amplitudes (dict): current target amplitudes
        """
        dt = 1.0 / self.sampling_rate
        t = self.t_cursor + np.arange(num_samples) * dt
        self.t_cursor += num_samples * dt

        # Scaled amplitudes to microvolts (uV)
        scale_uv = 40.0

        # Sine wave components
        s_delta = self.amplitudes['delta'] * scale_uv * np.sin(2.0 * np.pi * FREQ_TARGETS['delta'] * t + self.phases['delta'])
        s_theta = self.amplitudes['theta'] * scale_uv * np.sin(2.0 * np.pi * FREQ_TARGETS['theta'] * t + self.phases['theta'])
        s_alpha = self.amplitudes['alpha'] * scale_uv * np.sin(2.0 * np.pi * FREQ_TARGETS['alpha'] * t + self.phases['alpha'])
        s_beta  = self.amplitudes['beta']  * scale_uv * np.sin(2.0 * np.pi * FREQ_TARGETS['beta']  * t + self.phases['beta'])

        # Add Gaussian noise
        noise = np.random.normal(0, self.noise_level * 15.0, size=num_samples)

        waveform = s_delta + s_theta + s_alpha + s_beta + noise

        return waveform, self.amplitudes.copy()
