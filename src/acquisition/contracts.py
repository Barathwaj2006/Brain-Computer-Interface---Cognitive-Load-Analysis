"""
Canonical SignalFrame Contract and Generic SignalSource Abstraction for NeuroSim 2.0 (Phase 2)
Defines standardized frame payload schema and generic signal source interface.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
import time
import numpy as np
from PySide6.QtCore import QObject, Signal
from src.app.state import InputSource, ConnectionState, ConnectionTelemetry

@dataclass
class SignalFrame:
    """
    Canonical Data Acquisition Frame for NeuroSim 2.0.
    Standardized payload container delivered by signal sources into the signal buffer & pipeline.
    """
    timestamp: float = field(default_factory=time.time)
    sequence: int = 0
    sampling_rate: int = 250
    channel_count: int = 1
    channels: List[str] = field(default_factory=lambda: ["Ch1"])
    data: List[float] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    source: Any = InputSource.SIMULATOR
    metadata: Dict[str, Any] = field(default_factory=dict)
    transport: str = "Internal"
    device_id: Optional[str] = None
    latency_ms: float = 0.0
    integrity_status: str = "VALID"

    def __post_init__(self):
        self.validate()

    def validate(self):
        """Validates frame fields and enforces structural constraints."""
        if not isinstance(self.sampling_rate, (int, float)) or self.sampling_rate <= 0:
            raise ValueError(f"Invalid sampling_rate: {self.sampling_rate}. Must be > 0.")

        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise ValueError(f"Invalid sequence number: {self.sequence}. Must be an integer >= 0.")

        if not isinstance(self.timestamp, (int, float)) or self.timestamp <= 0:
            raise ValueError(f"Invalid timestamp: {self.timestamp}. Must be a positive float.")

        if self.data is None:
            raise ValueError("Frame data cannot be None.")

        # Convert numpy arrays to list for uniform handling
        if isinstance(self.data, np.ndarray):
            if self.data.ndim > 1:
                raise ValueError("Frame data must be 1-dimensional for single/multi-channel sample arrays.")
            self.data = [float(x) for x in self.data]
        elif isinstance(self.data, (list, tuple)):
            try:
                self.data = [float(x) for x in self.data]
            except (TypeError, ValueError) as e:
                raise ValueError(f"Malformed sample data in frame: {e}")
        else:
            raise ValueError(f"Invalid data type: {type(self.data)}. Must be list, tuple, or numpy array.")

        if not self.channels:
            self.channels = [f"Ch{i+1}" for i in range(self.channel_count)]

# Alias for backward compatibility
NormalizedFrame = SignalFrame

class BaseSignalSource(QObject):
    """
    Generic Abstract Base Interface for all NeuroSim 2.0 Signal Sources.
    Defines standard lifecycle methods and frame callbacks independent of UI and transport layers.
    """
    frame_received = Signal(object) # Emits SignalFrame
    state_changed = Signal(str)     # Emits status description

    def __init__(self, source_name: str = "GenericSource", parent=None):
        super().__init__(parent)
        self.source_name = source_name
        self._running = False
        self._paused = False
        self._callbacks: List[Callable[[SignalFrame], None]] = []

    def add_callback(self, callback: Callable[[SignalFrame], None]):
        """Registers a non-Qt python callback function for received frames."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[SignalFrame], None]):
        """Unregisters a python callback function."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def emit_frame(self, frame: SignalFrame):
        """Emits frame via Qt signal and non-Qt callbacks."""
        self.frame_received.emit(frame)
        for cb in self._callbacks:
            try:
                cb(frame)
            except Exception as e:
                print(f"[SignalSource Callback Error] {e}")

    def start(self) -> bool:
        """Starts signal generation/acquisition."""
        raise NotImplementedError("Subclasses must implement start()")

    def stop(self) -> bool:
        """Stops signal generation/acquisition."""
        raise NotImplementedError("Subclasses must implement stop()")

    def pause(self) -> bool:
        """Pauses signal emission."""
        raise NotImplementedError("Subclasses must implement pause()")

    def resume(self) -> bool:
        """Resumes signal emission from paused state."""
        raise NotImplementedError("Subclasses must implement resume()")

    def is_running(self) -> bool:
        return self._running

    def is_paused(self) -> bool:
        return self._paused


class BaseConnectionAdapter(QObject):
    """
    Common Abstract Base Interface for all Transport Adapters.
    """
    frame_received = Signal(object)
    connection_state_changed = Signal(object, str)
    error_occurred = Signal(str)
    telemetry_updated = Signal(object)

    def __init__(self, source: InputSource, transport_name: str, parent=None):
        super().__init__(parent)
        self._source = source
        self._transport_name = transport_name
        self._state = ConnectionState.IDLE
        self._telemetry = ConnectionTelemetry(source=source, transport=transport_name)

    @property
    def source(self) -> InputSource:
        return self._source

    @property
    def transport_name(self) -> str:
        return self._transport_name

    def connect_adapter(self, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def disconnect_adapter(self) -> bool:
        raise NotImplementedError()

    def start_stream(self) -> bool:
        raise NotImplementedError()

    def stop_stream(self) -> bool:
        raise NotImplementedError()

    def status(self) -> ConnectionState:
        return self._state

    def is_connected(self) -> bool:
        return self._state in (ConnectionState.CONNECTED, ConnectionState.STREAMING)

    def is_streaming(self) -> bool:
        return self._state == ConnectionState.STREAMING

    def get_telemetry(self) -> ConnectionTelemetry:
        return self._telemetry
