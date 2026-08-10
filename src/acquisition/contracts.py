"""
Unified Acquisition Contract and Base Connection Adapter Interface for NeuroSim 2.0
Establishes standardized frame payload schema and common adapter interface across all input transports.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import time
from PySide6.QtCore import QObject, Signal
from src.app.state import InputSource, ConnectionState, ConnectionTelemetry

@dataclass
class NormalizedFrame:
    """
    Normalized Data Acquisition Frame for NeuroSim 2.0.
    Standardized container delivered by all transport adapters into the signal pipeline.
    """
    source: InputSource = InputSource.NONE
    transport: str = "Unknown"
    device_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    sequence: int = 0
    sampling_rate: int = 250
    channel_count: int = 1
    channels: List[str] = field(default_factory=lambda: ["Ch1"])
    data: List[float] = field(default_factory=list)
    events: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    latency_ms: float = 0.0
    integrity_status: str = "VALID"  # "VALID", "INVALID_CHECKSUM", "SEQUENCE_GAP", "MALFORMED"

class BaseConnectionAdapter(QObject):
    """
    Common Abstract Base Interface for all NeuroSim 2.0 Transport Adapters.
    Encapsulates low-level worker threads behind uniform Qt signals and methods.
    """
    frame_received = Signal(object)           # Emits NormalizedFrame
    connection_state_changed = Signal(object, str) # (ConnectionState, status_text)
    error_occurred = Signal(str)             # Emits error description string
    telemetry_updated = Signal(object)        # Emits ConnectionTelemetry object

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
        """Initiates connection to target device/endpoint."""
        raise NotImplementedError("Subclasses must implement connect_adapter()")

    def disconnect_adapter(self) -> bool:
        """Disconnects transport and stops stream worker threads."""
        raise NotImplementedError("Subclasses must implement disconnect_adapter()")

    def start_stream(self) -> bool:
        """Starts active data streaming."""
        raise NotImplementedError("Subclasses must implement start_stream()")

    def stop_stream(self) -> bool:
        """Stops active data streaming without dropping connection."""
        raise NotImplementedError("Subclasses must implement stop_stream()")

    def status(self) -> ConnectionState:
        return self._state

    def is_connected(self) -> bool:
        return self._state in (ConnectionState.CONNECTED, ConnectionState.STREAMING)

    def is_streaming(self) -> bool:
        return self._state == ConnectionState.STREAMING

    def get_telemetry(self) -> ConnectionTelemetry:
        return self._telemetry
