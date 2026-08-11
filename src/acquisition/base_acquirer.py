"""
Generic Data Acquisition Interface for NeuroSim 2.0 (Phase 1C)
Standardizes streaming data sources and generic lifecycle control for Simulation and Hardware Modes.
"""

from typing import Callable, List, Optional, Any
from PySide6.QtCore import QObject, Signal
from src.core.enums import SignalSourceType
from src.core.signal_contract import SignalFrame

class BaseSignalSource(QObject):
    """
    Generic Abstract Base Interface for all NeuroSim 2.0 Signal Sources.
    Defines standard lifecycle methods and frame callbacks independent of UI and transport layers.
    """
    frame_received = Signal(object)    # Emits SignalFrame
    status_changed = Signal(str, bool) # (status_message, is_connected)

    def __init__(self, source_type: SignalSourceType = SignalSourceType.SIMULATOR, source_name: str = "GenericSource", parent=None):
        super().__init__(parent)
        self.source_type = source_type
        self.source_name = source_name
        self._running = False
        self._paused = False
        self._callbacks: List[Callable[[SignalFrame], None]] = []

    def add_callback(self, callback: Callable[[SignalFrame], None]):
        """Registers a python callback function for received frames."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[SignalFrame], None]):
        """Unregisters a python callback function."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def emit_frame(self, frame: SignalFrame):
        """Emits frame via Qt signal and non-Qt callbacks."""
        try:
            self.frame_received.emit(frame)
        except (RuntimeError, AttributeError):
            pass

        for cb in list(self._callbacks):
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

    def status(self) -> str:
        if not self._running:
            return "IDLE"
        if self._paused:
            return "PAUSED"
        return "STREAMING"

# Alias for backward compatibility
BaseAcquirer = BaseSignalSource
