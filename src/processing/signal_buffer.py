"""
Thread-Safe Bounded Rolling Signal Buffer for NeuroSim 2.0 (Phase 1C)
Thread-safe ring buffer managing channel-aligned EEG time-series data, timestamps, sequence numbers, and stream metadata.
"""

import threading
from collections import deque
from typing import List, Dict, Tuple, Optional, Any, Union
import numpy as np
from src.core.signal_contract import SignalFrame

DEFAULT_BUFFER_CAPACITY = 1250  # 5 seconds at 250 Hz
DEFAULT_SAMPLING_RATE = 250     # 250 Hz

class BoundedSignalBuffer:
    """
    Thread-safe bounded ring-buffer for multi-channel EEG time-series samples.
    Preserves channel alignment, chronological ordering, timestamps, and sequence numbers.
    """

    def __init__(self, capacity: int = DEFAULT_BUFFER_CAPACITY, sampling_rate: int = DEFAULT_SAMPLING_RATE, channels: Tuple[str, ...] = ("Ch1",)):
        if capacity <= 0:
            raise ValueError(f"Invalid capacity: {capacity}. Must be > 0.")
        if sampling_rate <= 0:
            raise ValueError(f"Invalid sampling_rate: {sampling_rate}. Must be > 0.")

        self._capacity = capacity
        self._sampling_rate = sampling_rate
        self._channels = tuple(channels) if channels else ("Ch1",)
        self._channel_count = len(self._channels)

        self._lock = threading.RLock()
        
        # Per-channel data deques
        self._data_deques: List[deque] = [deque(maxlen=capacity) for _ in range(self._channel_count)]
        self._time_deque: deque = deque(maxlen=capacity)
        self._seq_deque: deque = deque(maxlen=capacity)
        
        self._metadata: Dict[str, Any] = {}

    @property
    def capacity(self) -> int:
        with self._lock:
            return self._capacity

    @property
    def sampling_rate(self) -> int:
        with self._lock:
            return self._sampling_rate

    @sampling_rate.setter
    def sampling_rate(self, rate: int):
        if rate <= 0:
            raise ValueError(f"Invalid sampling_rate: {rate}. Must be > 0.")
        with self._lock:
            self._sampling_rate = int(rate)

    @property
    def channel_count(self) -> int:
        with self._lock:
            return self._channel_count

    @property
    def channels(self) -> Tuple[str, ...]:
        with self._lock:
            return self._channels

    @property
    def duration_sec(self) -> float:
        with self._lock:
            if not self._time_deque:
                return 0.0
            return len(self._time_deque) / self._sampling_rate

    @property
    def latest_timestamp(self) -> Optional[float]:
        with self._lock:
            return self._time_deque[-1] if self._time_deque else None

    def __len__(self) -> int:
        """Returns the number of samples stored per channel."""
        with self._lock:
            return len(self._time_deque)

    def _ensure_channel_capacity(self, channels: Tuple[str, ...]):
        """Adjusts per-channel deques if new channel labels arrive."""
        if channels != self._channels:
            self._channels = tuple(channels)
            self._channel_count = len(self._channels)
            # Re-initialize data deques while preserving capacity
            new_deques = [deque(maxlen=self._capacity) for _ in range(self._channel_count)]
            self._data_deques = new_deques
            self._time_deque.clear()
            self._seq_deque.clear()

    def append_frame(self, frame: SignalFrame):
        """
        Appends a canonical SignalFrame payload into the rolling buffer.
        Preserves channel alignment, sequence numbers, and timestamps.
        """
        if not isinstance(frame, SignalFrame):
            raise TypeError(f"Expected SignalFrame, got {type(frame)}")

        with self._lock:
            # Check channel alignment
            if frame.channels != self._channels or frame.channel_count != self._channel_count:
                if len(self._time_deque) == 0:
                    self._ensure_channel_capacity(frame.channels)
                else:
                    # If channels change mid-stream, re-align
                    self._ensure_channel_capacity(frame.channels)

            num_samples = frame.num_samples
            dt = 1.0 / frame.sampling_rate if frame.sampling_rate > 0 else 1.0 / self._sampling_rate
            
            for s_idx in range(num_samples):
                # Channel-aligned append
                for c_idx in range(self._channel_count):
                    val = frame.data[c_idx][s_idx]
                    self._data_deques[c_idx].append(float(val))

                ts = frame.timestamp + s_idx * dt
                seq = frame.sequence + s_idx
                self._time_deque.append(float(ts))
                self._seq_deque.append(int(seq))

            if frame.metadata:
                self._metadata.update(dict(frame.metadata))

    def append_samples(self, data: Any, timestamp: float, sequence: int, channels: Optional[Tuple[str, ...]] = None):
        """
        Appends raw sample matrix into the buffer.
        `data` can be 1D (single channel) or 2D (multi-channel).
        """
        if channels:
            target_channels = tuple(channels)
        else:
            target_channels = self._channels

        dummy_frame = SignalFrame(
            timestamp=timestamp,
            sequence=sequence,
            sampling_rate=self._sampling_rate,
            channel_count=len(target_channels),
            channels=target_channels,
            data=data
        )
        self.append_frame(dummy_frame)

    def get_samples(self, channel_idx: int = 0) -> np.ndarray:
        """Returns 1D float64 NumPy array for a specific channel index."""
        with self._lock:
            if not 0 <= channel_idx < self._channel_count:
                raise IndexError(f"Channel index {channel_idx} out of range (0 to {self._channel_count - 1}).")
            return np.array(self._data_deques[channel_idx], dtype=np.float64)

    def get_all_samples(self) -> np.ndarray:
        """Returns 2D float64 NumPy array of shape (channel_count, num_samples)."""
        with self._lock:
            if len(self._time_deque) == 0:
                return np.zeros((self._channel_count, 0), dtype=np.float64)
            arr_list = [np.array(dq, dtype=np.float64) for dq in self._data_deques]
            return np.array(arr_list, dtype=np.float64)

    def get_timestamps(self) -> np.ndarray:
        """Returns 1D float64 NumPy array of sample timestamps."""
        with self._lock:
            return np.array(self._time_deque, dtype=np.float64)

    def get_sequences(self) -> np.ndarray:
        """Returns 1D int64 NumPy array of sample sequence numbers."""
        with self._lock:
            return np.array(self._seq_deque, dtype=np.int64)

    def get_window(self, seconds: float = 5.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Returns (samples_2d, timestamps, sequence_numbers) for the requested duration.
        """
        with self._lock:
            if len(self._time_deque) == 0:
                return np.zeros((self._channel_count, 0), dtype=np.float64), np.array([], dtype=np.float64), np.array([], dtype=np.int64)

            sample_count = int(min(len(self._time_deque), int(seconds * self._sampling_rate)))
            if sample_count <= 0:
                return np.zeros((self._channel_count, 0), dtype=np.float64), np.array([], dtype=np.float64), np.array([], dtype=np.int64)

            ch_samples = [np.array(list(dq)[-sample_count:], dtype=np.float64) for dq in self._data_deques]
            s_arr = np.array(ch_samples, dtype=np.float64)
            t_arr = np.array(list(self._time_deque)[-sample_count:], dtype=np.float64)
            q_arr = np.array(list(self._seq_deque)[-sample_count:], dtype=np.int64)
            return s_arr, t_arr, q_arr

    def snapshot(self) -> Dict[str, Any]:
        """
        Returns a thread-safe atomic snapshot dictionary of the current buffer state.
        """
        with self._lock:
            all_s = self.get_all_samples()
            primary_s = self.get_samples(0) if self._channel_count > 0 else np.array([])
            ts = self.get_timestamps()
            seq = self.get_sequences()

            return {
                "samples": primary_s,
                "all_samples": all_s,
                "timestamps": ts,
                "sequences": seq,
                "channels": self._channels,
                "channel_count": self._channel_count,
                "sampling_rate": self._sampling_rate,
                "duration_sec": self.duration_sec,
                "latest_timestamp": self.latest_timestamp,
                "count": len(self._time_deque),
                "metadata": dict(self._metadata)
            }

    def clear(self):
        """Clears all stored samples, timestamps, sequence numbers, and metadata."""
        with self._lock:
            for dq in self._data_deques:
                dq.clear()
            self._time_deque.clear()
            self._seq_deque.clear()
            self._metadata.clear()

# Alias for Phase 1C specification
SignalBuffer = BoundedSignalBuffer
