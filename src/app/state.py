"""
Centralized Application State, State Machine Controller, and Telemetry Model for NeuroSim 2.0
Defines strongly-typed connection states, input sources, transition validation, and telemetry model.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Set, Dict, Optional
import time
from PySide6.QtCore import QObject, Signal

class ConnectionState(Enum):
    IDLE = auto()
    SCANNING = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    STREAMING = auto()
    PAUSED = auto()
    DISCONNECTING = auto()
    ERROR = auto()

class InputSource(Enum):
    NONE = auto()
    POKIDEX_WIFI = auto()
    POKIDEX_BLE = auto()
    ESP32_USB = auto()
    ESP32_WIFI = auto()
    SIMULATOR = auto()

@dataclass
class ConnectionTelemetry:
    """Unified Telemetry Model for NeuroSim 2.0 Connection Core."""
    source: InputSource = InputSource.NONE
    transport: str = "Unknown"
    device_id: str = "Unknown"
    connection_state: ConnectionState = ConnectionState.IDLE
    streaming: bool = False
    sampling_rate: int = 250
    packets_received: int = 0
    packets_dropped: int = 0
    drop_percentage: float = 0.0
    invalid_packets: int = 0
    sequence_gaps: int = 0
    latency_ms: float = 0.0
    last_packet_time: float = 0.0
    session_duration: float = 0.0
    last_error: str = ""

    def update_drop_percentage(self):
        total = self.packets_received + self.packets_dropped
        if total > 0:
            self.drop_percentage = round((self.packets_dropped / total) * 100.0, 2)
        else:
            self.drop_percentage = 0.0

# Valid transition mapping for deterministic state machine
VALID_TRANSITIONS: Dict[ConnectionState, Set[ConnectionState]] = {
    ConnectionState.IDLE: {ConnectionState.SCANNING, ConnectionState.CONNECTING, ConnectionState.CONNECTED, ConnectionState.STREAMING, ConnectionState.ERROR},
    ConnectionState.SCANNING: {ConnectionState.CONNECTING, ConnectionState.CONNECTED, ConnectionState.IDLE, ConnectionState.ERROR},
    ConnectionState.CONNECTING: {ConnectionState.CONNECTED, ConnectionState.IDLE, ConnectionState.DISCONNECTING, ConnectionState.ERROR},
    ConnectionState.CONNECTED: {ConnectionState.STREAMING, ConnectionState.DISCONNECTING, ConnectionState.IDLE, ConnectionState.ERROR},
    ConnectionState.STREAMING: {ConnectionState.PAUSED, ConnectionState.DISCONNECTING, ConnectionState.IDLE, ConnectionState.ERROR},
    ConnectionState.PAUSED: {ConnectionState.STREAMING, ConnectionState.DISCONNECTING, ConnectionState.IDLE, ConnectionState.ERROR},
    ConnectionState.DISCONNECTING: {ConnectionState.IDLE, ConnectionState.ERROR},
    ConnectionState.ERROR: {ConnectionState.IDLE, ConnectionState.SCANNING, ConnectionState.CONNECTING}
}

class CentralStateManager(QObject):
    """
    Thread-safe Qt controller managing application connection state and active input source.
    Emits signals on state transitions and telemetry updates for reactive UI updates.
    """
    state_changed = Signal(object, object)      # (old_state: ConnectionState, new_state: ConnectionState)
    source_changed = Signal(object, object)     # (old_source: InputSource, new_source: InputSource)
    status_text_changed = Signal(str)           # Human-readable status badge message
    telemetry_updated = Signal(object)          # ConnectionTelemetry object

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = ConnectionState.IDLE
        self._source = InputSource.NONE
        self._status_text = "● DISCONNECTED / IDLE"
        self._telemetry = ConnectionTelemetry()

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def source(self) -> InputSource:
        return self._source

    @property
    def status_text(self) -> str:
        return self._status_text

    @property
    def telemetry(self) -> ConnectionTelemetry:
        return self._telemetry

    def set_source(self, new_source: InputSource) -> bool:
        """Sets the active input source explicitly."""
        if self._source == new_source:
            return True
        old_source = self._source
        self._source = new_source
        self._telemetry.source = new_source
        self.source_changed.emit(old_source, new_source)
        return True

    def update_telemetry(self, telemetry: ConnectionTelemetry):
        """Updates and emits unified connection telemetry."""
        self._telemetry = telemetry
        self._telemetry.connection_state = self._state
        self._telemetry.source = self._source
        self.telemetry_updated.emit(self._telemetry)

    def transition_to(self, new_state: ConnectionState, status_text: str = "") -> bool:
        """
        Executes a controlled state transition if valid.
        Returns True if successful, False if transition is rejected.
        """
        if self._state == new_state:
            if status_text and status_text != self._status_text:
                self._status_text = status_text
                self.status_text_changed.emit(self._status_text)
            return True

        allowed = VALID_TRANSITIONS.get(self._state, set())
        if new_state not in allowed:
            print(f"[StateManager REJECTED] Invalid transition from {self._state.name} to {new_state.name}")
            return False

        old_state = self._state
        self._state = new_state
        self._telemetry.connection_state = new_state
        self._telemetry.streaming = (new_state == ConnectionState.STREAMING)

        if status_text:
            self._status_text = status_text
        else:
            self._status_text = f"● {new_state.name}"

        self.state_changed.emit(old_state, new_state)
        self.status_text_changed.emit(self._status_text)
        self.telemetry_updated.emit(self._telemetry)
        return True

    def reset_to_idle(self, status_text: str = "● DISCONNECTED / IDLE"):
        """Resets both source, state, and telemetry to default zero-input IDLE baseline."""
        old_state = self._state
        old_source = self._source
        
        self._source = InputSource.NONE
        self._state = ConnectionState.IDLE
        self._status_text = status_text
        self._telemetry = ConnectionTelemetry(connection_state=ConnectionState.IDLE)

        if old_source != InputSource.NONE:
            self.source_changed.emit(old_source, InputSource.NONE)
        if old_state != ConnectionState.IDLE:
            self.state_changed.emit(old_state, ConnectionState.IDLE)
        self.status_text_changed.emit(self._status_text)
        self.telemetry_updated.emit(self._telemetry)
