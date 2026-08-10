"""
Bounded Signal Buffer Service for NeuroSim 2.0
Thread-safe, bounded-capacity ring buffer managing active EEG time-series data and stream metadata.
"""

import threading
from collections import deque
from typing import List, Dict, Optional
import numpy as np
from PySide6.QtCore import QObject, Signal
from src.app.state import InputSource

DEFAULT_BUFFER_CAPACITY = 1250  # 5 seconds at 250 Hz sampling rate
DEFAULT_SAMPLING_RATE = 250     # 250 Hz

class BoundedSignalBuffer(QObject):
    """
    Thread-safe bounded ring-buffer for EEG floating-point samples.
    Protects multi-threaded ingestion from GUI/DSP processing thread contention.
    """
    buffer_updated = Signal(int)  # Emits current sample count on update
    buffer_cleared = Signal()     # Emits when buffer is explicitly cleared

    def __init__(self, capacity: int = DEFAULT_BUFFER_CAPACITY, sampling_rate: int = DEFAULT_SAMPLING_RATE, parent=None):
        super().__init__(parent)
        self._capacity = capacity
        self._sampling_rate = sampling_rate
        self._lock = threading.Lock()
        self._deque: deque = deque(maxlen=capacity)
        self._active_source = InputSource.NONE
        self._source_metadata: Dict = {}

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def sampling_rate(self) -> int:
        return self._sampling_rate

    @sampling_rate.setter
    def sampling_rate(self, rate: int):
        with self._lock:
            self._sampling_rate = max(1, rate)

    @property
    def active_source(self) -> InputSource:
        with self._lock:
            return self._active_source

    @property
    def metadata(self) -> Dict:
        with self._lock:
            return dict(self._source_metadata)

    def __len__(self) -> int:
        with self._lock:
            return len(self._deque)

    def append(self, sample: float, source: InputSource = InputSource.NONE, metadata: Optional[Dict] = None):
        """Appends a single sample value to the buffer."""
        with self._lock:
            self._deque.append(float(sample))
            if source != InputSource.NONE:
                self._active_source = source
            if metadata:
                self._source_metadata.update(metadata)
            count = len(self._deque)

        self.buffer_updated.emit(count)

    def extend(self, samples: List[float], source: InputSource = InputSource.NONE, metadata: Optional[Dict] = None):
        """Extends the buffer with a chunk of samples."""
        if not samples:
            return
        with self._lock:
            for s in samples:
                self._deque.append(float(s))
            if source != InputSource.NONE:
                self._active_source = source
            if metadata:
                self._source_metadata.update(metadata)
            count = len(self._deque)

        self.buffer_updated.emit(count)

    def get_samples(self) -> np.ndarray:
        """Returns a copy of current buffer samples as a 1D NumPy array."""
        with self._lock:
            return np.array(self._deque, dtype=np.float64)

    def get_latest_samples(self, count: int) -> np.ndarray:
        """Returns the most recent `count` samples."""
        with self._lock:
            if not self._deque:
                return np.array([], dtype=np.float64)
            items = list(self._deque)[-count:]
            return np.array(items, dtype=np.float64)

    def clear(self):
        """Clears all stored samples and resets active source metadata."""
        with self._lock:
            self._deque.clear()
            self._active_source = InputSource.NONE
            self._source_metadata.clear()

        self.buffer_cleared.emit()
