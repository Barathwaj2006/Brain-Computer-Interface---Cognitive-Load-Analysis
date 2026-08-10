"""
Thread-Safe Bounded Rolling Signal Buffer for NeuroSim 2.0 (Phase 2)
Thread-safe, bounded-capacity ring buffer managing active EEG time-series data, timestamp history, sequence numbers, and stream metadata.
"""

import threading
from collections import deque
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
from PySide6.QtCore import QObject, Signal
from src.app.state import InputSource

DEFAULT_BUFFER_CAPACITY = 1250  # 5 seconds at 250 Hz sampling rate
DEFAULT_SAMPLING_RATE = 250     # 250 Hz

class BoundedSignalBuffer(QObject):
    """
    Thread-safe bounded ring-buffer for EEG floating-point samples, timestamps, and sequence numbers.
    Protects multi-threaded ingestion from GUI/DSP processing thread contention.
    """
    buffer_updated = Signal(int)  # Emits current sample count on update
    buffer_cleared = Signal()     # Emits when buffer is explicitly cleared

    def __init__(self, capacity: int = DEFAULT_BUFFER_CAPACITY, sampling_rate: int = DEFAULT_SAMPLING_RATE, parent=None):
        super().__init__(parent)
        self._capacity = capacity
        self._sampling_rate = sampling_rate
        self._lock = threading.Lock()
        
        # Internal ring buffers for values, timestamps, and sequence numbers
        self._data_deque: deque = deque(maxlen=capacity)
        self._time_deque: deque = deque(maxlen=capacity)
        self._seq_deque: deque = deque(maxlen=capacity)
        
        self._active_source: Any = InputSource.NONE
        self._source_metadata: Dict[str, Any] = {}

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def sampling_rate(self) -> int:
        return self._sampling_rate

    @sampling_rate.setter
    def sampling_rate(self, rate: int):
        with self._lock:
            self._sampling_rate = max(1, int(rate))

    @property
    def active_source(self) -> Any:
        with self._lock:
            return self._active_source

    @property
    def metadata(self) -> Dict:
        with self._lock:
            return dict(self._source_metadata)

    def __len__(self) -> int:
        with self._lock:
            return len(self._data_deque)

    def append(self, sample: float, source: Any = InputSource.NONE, metadata: Optional[Dict] = None, timestamp: Optional[float] = None, sequence: Optional[int] = None):
        """Appends a single sample value to the buffer."""
        import time
        t_now = timestamp if timestamp is not None else time.time()
        seq_num = sequence if sequence is not None else (self._seq_deque[-1] + 1 if self._seq_deque else 0)

        with self._lock:
            self._data_deque.append(float(sample))
            self._time_deque.append(float(t_now))
            self._seq_deque.append(int(seq_num))
            
            if source != InputSource.NONE:
                self._active_source = source
            if metadata:
                self._source_metadata.update(metadata)
            count = len(self._data_deque)

        self.buffer_updated.emit(count)

    def extend(self, samples, source: Any = InputSource.NONE, metadata: Optional[Dict] = None, timestamps: Optional[List[float]] = None, sequences: Optional[List[int]] = None):
        """Extends the buffer with a chunk of samples."""
        if samples is None or len(samples) == 0:
            return

        import time
        t_now = time.time()
        with self._lock:
            for i, s in enumerate(samples):
                ts = timestamps[i] if (timestamps and i < len(timestamps)) else (t_now + i * (1.0 / self._sampling_rate))
                sq = sequences[i] if (sequences and i < len(sequences)) else (self._seq_deque[-1] + 1 if self._seq_deque else i)
                
                self._data_deque.append(float(s))
                self._time_deque.append(float(ts))
                self._seq_deque.append(int(sq))

            if source != InputSource.NONE:
                self._active_source = source
            if metadata:
                self._source_metadata.update(metadata)
            count = len(self._data_deque)

        self.buffer_updated.emit(count)

    def append_frame(self, frame):
        """Appends a SignalFrame / NormalizedFrame payload into the buffer."""
        if frame is None or not frame.data:
            return

        seqs = [frame.sequence + i for i in range(len(frame.data))]
        dt = 1.0 / frame.sampling_rate if frame.sampling_rate > 0 else 1.0 / self._sampling_rate
        times = [frame.timestamp + i * dt for i in range(len(frame.data))]
        
        self.extend(
            samples=frame.data,
            source=frame.source,
            metadata=frame.metadata,
            timestamps=times,
            sequences=seqs
        )

    def get_samples(self) -> np.ndarray:
        """Returns a copy of current buffer samples as a 1D NumPy array."""
        with self._lock:
            return np.array(self._data_deque, dtype=np.float64)

    def get_timestamps(self) -> np.ndarray:
        """Returns a copy of current sample timestamps as a 1D NumPy array."""
        with self._lock:
            return np.array(self._time_deque, dtype=np.float64)

    def get_sequences(self) -> np.ndarray:
        """Returns a copy of current sample sequence numbers as a 1D NumPy array."""
        with self._lock:
            return np.array(self._seq_deque, dtype=np.int64)

    def get_latest_samples(self, count: int) -> np.ndarray:
        """Returns the most recent `count` samples."""
        with self._lock:
            if not self._data_deque:
                return np.array([], dtype=np.float64)
            items = list(self._data_deque)[-count:]
            return np.array(items, dtype=np.float64)

    def get_window(self, seconds: float = 5.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Returns (samples, timestamps, sequence_numbers) for the requested window duration.
        """
        with self._lock:
            if not self._data_deque:
                return np.array([]), np.array([]), np.array([])
            count = int(min(len(self._data_deque), seconds * self._sampling_rate))
            s_arr = np.array(list(self._data_deque)[-count:], dtype=np.float64)
            t_arr = np.array(list(self._time_deque)[-count:], dtype=np.float64)
            q_arr = np.array(list(self._seq_deque)[-count:], dtype=np.int64)
            return s_arr, t_arr, q_arr

    def clear(self):
        """Clears all stored samples, timestamps, and sequence metadata."""
        with self._lock:
            self._data_deque.clear()
            self._time_deque.clear()
            self._seq_deque.clear()
            self._active_source = InputSource.NONE
            self._source_metadata.clear()

        self.buffer_cleared.emit()

# Alias for Phase 2 specification
SignalBuffer = BoundedSignalBuffer
