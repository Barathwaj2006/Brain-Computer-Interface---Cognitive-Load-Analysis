"""
Signal Preprocessing & Filtering Module
Detrending, DC Removal, and Butterworth Bandpass Filtering
"""

import numpy as np
from scipy import signal
from src.app.config import SAMPLING_RATE_HZ

class EEGFilter:
    def __init__(self, sampling_rate: int = SAMPLING_RATE_HZ, lowcut: float = 0.5, highcut: float = 40.0, order: int = 4):
        self.sampling_rate = sampling_rate
        self.lowcut = lowcut
        self.highcut = highcut
        self.order = order
        
        # Design Butterworth bandpass filter
        nyq = 0.5 * sampling_rate
        low = lowcut / nyq
        high = highcut / nyq
        self.b, self.a = signal.butter(order, [low, high], btype='band')

    def process(self, raw_signal: np.ndarray) -> np.ndarray:
        """
        Detrend, remove DC offset, and apply bandpass filter.
        """
        if len(raw_signal) < 16:
            return raw_signal
            
        # 1. Detrend (remove linear trend & DC offset)
        detrended = signal.detrend(raw_signal, type='constant')
        
        # 2. Apply Butterworth Bandpass filter
        filtered = signal.filtfilt(self.b, self.a, detrended)
        return filtered
