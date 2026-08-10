"""
Centralized Application State and State Machine Controller for NeuroSim 2.0
Defines strongly-typed connection states, input sources, and controlled transitions.
"""

from enum import Enum, auto
from typing import Set, Dict
from PySide6.QtCore import QObject, Signal

class ConnectionState(Enum):
    IDLE = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    STREAMING = auto()
    PAUSED = auto()
    ERROR = auto()

class InputSource(Enum):
    NONE = auto()
    POKIDEX_WIFI = auto()
    POKIDEX_BLE = auto()
    ESP32_USB = auto()
    ESP32_WIFI = auto()
    SIMULATOR = auto()

# Valid transition mapping: source_state -> set of valid target_states
VALID_TRANSITIONS: Dict[ConnectionState, Set[ConnectionState]] = {
    ConnectionState.IDLE: {ConnectionState.CONNECTING, ConnectionState.CONNECTED, ConnectionState.STREAMING, ConnectionState.ERROR},
    ConnectionState.CONNECTING: {ConnectionState.CONNECTED, ConnectionState.IDLE, ConnectionState.ERROR},
    ConnectionState.CONNECTED: {ConnectionState.STREAMING, ConnectionState.IDLE, ConnectionState.ERROR},
    ConnectionState.STREAMING: {ConnectionState.PAUSED, ConnectionState.IDLE, ConnectionState.ERROR},
    ConnectionState.PAUSED: {ConnectionState.STREAMING, ConnectionState.IDLE, ConnectionState.ERROR},
    ConnectionState.ERROR: {ConnectionState.IDLE, ConnectionState.CONNECTING}
}

class CentralStateManager(QObject):
    """
    Thread-safe Qt controller managing application connection state and active input source.
    Emits signals on state transitions for reactive UI updates.
    """
    state_changed = Signal(object, object)      # (old_state: ConnectionState, new_state: ConnectionState)
    source_changed = Signal(object, object)     # (old_source: InputSource, new_source: InputSource)
    status_text_changed = Signal(str)           # Human-readable status badge message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = ConnectionState.IDLE
        self._source = InputSource.NONE
        self._status_text = "● DISCONNECTED / IDLE"

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def source(self) -> InputSource:
        return self._source

    @property
    def status_text(self) -> str:
        return self._status_text

    def set_source(self, new_source: InputSource) -> bool:
        """Sets the active input source explicitly."""
        if self._source == new_source:
            return True
        old_source = self._source
        self._source = new_source
        self.source_changed.emit(old_source, new_source)
        return True

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
        if status_text:
            self._status_text = status_text
        else:
            self._status_text = f"● {new_state.name}"

        self.state_changed.emit(old_state, new_state)
        self.status_text_changed.emit(self._status_text)
        return True

    def reset_to_idle(self, status_text: str = "● DISCONNECTED / IDLE"):
        """Resets both source and state to default zero-input IDLE baseline."""
        old_state = self._state
        old_source = self._source
        
        self._source = InputSource.NONE
        self._state = ConnectionState.IDLE
        self._status_text = status_text

        if old_source != InputSource.NONE:
            self.source_changed.emit(old_source, InputSource.NONE)
        if old_state != ConnectionState.IDLE:
            self.state_changed.emit(old_state, ConnectionState.IDLE)
        self.status_text_changed.emit(self._status_text)
