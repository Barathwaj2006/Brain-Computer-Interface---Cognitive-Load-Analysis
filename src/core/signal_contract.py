"""
Canonical Signal Frame Contract for NeuroSim 2.0 (Phase 1A)
Defines an immutable, validated, generic data container for single-channel and multi-channel EEG signals.
"""

import json
import time
import math
import types
from dataclasses import dataclass, field
from typing import Tuple, List, Dict, Any, Union, Optional
import numpy as np
from src.core.enums import SignalSourceType

@dataclass(frozen=True)
class SignalFrame:
    """
    Canonical Immutable EEG Signal Frame for NeuroSim 2.0.
    Encapsulates time-series sample data, metadata, sequence numbers, and sampling configuration.
    Guarantees structural validation and immutability.
    """
    timestamp: float
    sequence: int
    sampling_rate: int
    channel_count: int
    channels: Tuple[str, ...]
    data: Tuple[Tuple[float, ...], ...]
    source: SignalSourceType = SignalSourceType.SIMULATOR
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Validate timestamp
        if not isinstance(self.timestamp, (int, float)) or self.timestamp <= 0 or math.isnan(self.timestamp) or math.isinf(self.timestamp):
            raise ValueError(f"Invalid timestamp: {self.timestamp}. Must be a positive finite float.")

        # Validate sequence
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool) or self.sequence < 0:
            raise ValueError(f"Invalid sequence: {self.sequence}. Must be a non-negative integer >= 0.")

        # Validate sampling rate
        if not isinstance(self.sampling_rate, int) or isinstance(self.sampling_rate, bool) or self.sampling_rate <= 0:
            raise ValueError(f"Invalid sampling_rate: {self.sampling_rate}. Must be an integer > 0.")

        # Validate channel count
        if not isinstance(self.channel_count, int) or isinstance(self.channel_count, bool) or self.channel_count <= 0:
            raise ValueError(f"Invalid channel_count: {self.channel_count}. Must be an integer > 0.")

        # Validate channels tuple
        if not isinstance(self.channels, tuple):
            try:
                object.__setattr__(self, 'channels', tuple(str(ch) for ch in self.channels))
            except Exception as e:
                raise ValueError(f"Invalid channels container: {e}")

        if len(self.channels) != self.channel_count:
            raise ValueError(f"Channels length ({len(self.channels)}) does not match channel_count ({self.channel_count}).")

        # Validate & normalize data tuple
        normalized_data = self._normalize_data(self.data, self.channel_count)
        object.__setattr__(self, 'data', normalized_data)

        # Ensure metadata is frozen mapping or copy
        if isinstance(self.metadata, dict):
            object.__setattr__(self, 'metadata', types.MappingProxyType(dict(self.metadata)))
        elif not isinstance(self.metadata, types.MappingProxyType):
            raise ValueError(f"Invalid metadata type: {type(self.metadata)}. Must be dict or MappingProxyType.")

        # Ensure source is valid SignalSourceType
        if not isinstance(self.source, SignalSourceType):
            if isinstance(self.source, str):
                object.__setattr__(self, 'source', SignalSourceType.from_str(self.source))
            else:
                raise ValueError(f"Invalid source type: {self.source}. Must be a SignalSourceType enum instance.")

    @staticmethod
    def _normalize_data(raw_data: Any, expected_channels: int) -> Tuple[Tuple[float, ...], ...]:
        """Validates numerical values and returns normalized 2D tuple (channel_count, num_samples)."""
        if raw_data is None:
            raise ValueError("Sample data cannot be None.")

        # Convert numpy array if supplied
        if isinstance(raw_data, np.ndarray):
            if raw_data.dtype.kind not in ('i', 'f'):
                raise ValueError(f"Non-numeric numpy dtype: {raw_data.dtype}")
            if raw_data.ndim == 1:
                raw_data = [raw_data.tolist()]
            elif raw_data.ndim == 2:
                raw_data = raw_data.tolist()
            else:
                raise ValueError(f"Unsupported numpy array dimensions: {raw_data.ndim}D")

        # Handle 1D list/tuple (single channel)
        if isinstance(raw_data, (list, tuple)):
            if len(raw_data) > 0 and not isinstance(raw_data[0], (list, tuple, np.ndarray)):
                if expected_channels == 1:
                    raw_data = [raw_data]
                else:
                    raise ValueError(f"Data provided as 1D list of length {len(raw_data)}, but expected {expected_channels} channels.")

        if not isinstance(raw_data, (list, tuple)) or len(raw_data) == 0:
            raise ValueError("Sample data must be a non-empty list or tuple of channel sample arrays.")

        if len(raw_data) != expected_channels:
            raise ValueError(f"Data channel count ({len(raw_data)}) does not match expected channel_count ({expected_channels}).")

        sample_length: Optional[int] = None
        channel_tuples = []

        for ch_idx, ch_samples in enumerate(raw_data):
            if isinstance(ch_samples, np.ndarray):
                ch_samples = ch_samples.tolist()
            if not isinstance(ch_samples, (list, tuple)):
                raise ValueError(f"Channel {ch_idx} samples must be list or tuple, got {type(ch_samples)}")

            if len(ch_samples) == 0:
                raise ValueError(f"Channel {ch_idx} has 0 samples.")

            if sample_length is None:
                sample_length = len(ch_samples)
            elif len(ch_samples) != sample_length:
                raise ValueError(f"Channel sample length mismatch: channel 0 has {sample_length} samples, channel {ch_idx} has {len(ch_samples)} samples.")

            float_samples = []
            for val_idx, val in enumerate(ch_samples):
                if isinstance(val, bool):
                    raise ValueError(f"Boolean sample at ch {ch_idx}, idx {val_idx}")
                try:
                    f_val = float(val)
                except (TypeError, ValueError):
                    raise ValueError(f"Non-numeric sample value at ch {ch_idx}, idx {val_idx}: {val}")

                if math.isnan(f_val) or math.isinf(f_val):
                    raise ValueError(f"Invalid non-finite sample value (NaN/Inf) at ch {ch_idx}, idx {val_idx}: {f_val}")

                float_samples.append(f_val)

            channel_tuples.append(tuple(float_samples))

        return tuple(channel_tuples)

    @property
    def num_samples(self) -> int:
        """Returns the number of samples per channel."""
        return len(self.data[0]) if self.data else 0

    def get_channel_data(self, channel_idx: int = 0) -> Tuple[float, ...]:
        """Returns sample values for a specific channel index."""
        if not 0 <= channel_idx < self.channel_count:
            raise IndexError(f"Channel index {channel_idx} out of range (0 to {self.channel_count - 1}).")
        return self.data[channel_idx]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes SignalFrame to a plain Python dictionary."""
        return {
            "timestamp": self.timestamp,
            "sequence": self.sequence,
            "sampling_rate": self.sampling_rate,
            "channel_count": self.channel_count,
            "channels": list(self.channels),
            "data": [list(ch) for ch in self.data],
            "source": self.source.name,
            "metadata": dict(self.metadata)
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SignalFrame":
        """Deserializes a dictionary into a validated SignalFrame instance."""
        if not isinstance(d, dict):
            raise ValueError(f"Expected dict for deserialization, got {type(d)}")

        required = {"timestamp", "sequence", "sampling_rate", "channel_count", "channels", "data"}
        missing = required - set(d.keys())
        if missing:
            raise ValueError(f"Missing required fields for SignalFrame deserialization: {missing}")

        source_val = d.get("source", SignalSourceType.SIMULATOR)
        if isinstance(source_val, str):
            source_obj = SignalSourceType.from_str(source_val)
        elif isinstance(source_val, SignalSourceType):
            source_obj = source_val
        else:
            source_obj = SignalSourceType.SIMULATOR

        return cls(
            timestamp=float(d["timestamp"]),
            sequence=int(d["sequence"]),
            sampling_rate=int(d["sampling_rate"]),
            channel_count=int(d["channel_count"]),
            channels=tuple(d["channels"]),
            data=tuple(tuple(float(x) for x in ch) for ch in d["data"]),
            source=source_obj,
            metadata=dict(d.get("metadata", {}))
        )

    def to_json(self) -> str:
        """Serializes SignalFrame to a JSON string representation."""
        return json.dumps(self.to_dict(), indent=None)

    @classmethod
    def from_json(cls, json_str: str) -> "SignalFrame":
        """Deserializes a JSON string into a SignalFrame instance."""
        try:
            parsed = json.loads(json_str)
        except Exception as e:
            raise ValueError(f"Invalid JSON string for SignalFrame: {e}")
        return cls.from_dict(parsed)
