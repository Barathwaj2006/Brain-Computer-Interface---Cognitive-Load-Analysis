"""
Centralized Signal Acquisition Manager for NeuroSim 2.0 (Phase 1C)
Orchestrates generic BaseSignalSource instances, handles lifecycle controls, and forwards SignalFrames into BoundedSignalBuffer.
"""

import threading
from typing import Dict, Optional, Any
from PySide6.QtCore import QObject, Signal
from src.core.enums import SignalSourceType
from src.core.signal_contract import SignalFrame
from src.processing.signal_buffer import BoundedSignalBuffer
from src.acquisition.base_acquirer import BaseSignalSource

class AcquisitionManager(QObject):
    """
    Centralized Acquisition Manager orchestrating signal acquisition.
    Routes canonical SignalFrame payloads into BoundedSignalBuffer and tracks acquisition telemetry.
    """
    frame_received = Signal(object) # Emits SignalFrame
    status_changed = Signal(str)    # Emits status message

    def __init__(self, signal_buffer: BoundedSignalBuffer, parent=None):
        super().__init__(parent)
        self.signal_buffer = signal_buffer
        self._sources: Dict[str, BaseSignalSource] = {}
        self.active_source: Optional[BaseSignalSource] = None
        self._lock = threading.RLock()

        # Telemetry counters
        self._frames_received = 0
        self._samples_received = 0
        self._last_sequence = -1
        self._sequence_gaps = 0

    @property
    def frames_received(self) -> int:
        with self._lock:
            return self._frames_received

    @property
    def samples_received(self) -> int:
        with self._lock:
            return self._samples_received

    @property
    def sequence_gaps(self) -> int:
        with self._lock:
            return self._sequence_gaps

    def reset_telemetry(self):
        """Resets stream telemetry counters for a fresh acquisition session."""
        with self._lock:
            self._frames_received = 0
            self._samples_received = 0
            self._sequence_gaps = 0
            self._last_sequence = -1

    def register_source(self, name: str, source: BaseSignalSource):
        """Registers a generic BaseSignalSource instance."""
        if not isinstance(source, BaseSignalSource):
            raise TypeError(f"Expected BaseSignalSource, got {type(source)}")
        with self._lock:
            self._sources[name] = source

    def select_source(self, name: str) -> bool:
        """Selects and binds an active signal source by name."""
        with self._lock:
            if name not in self._sources:
                return False

            if self.active_source:
                self.active_source.stop()
                try:
                    self.active_source.frame_received.disconnect(self._on_frame)
                except (RuntimeError, AttributeError):
                    pass

            self.active_source = self._sources[name]
            self.active_source.frame_received.connect(self._on_frame)
            self.active_source.add_callback(self._on_frame_cb)
            return True

    def start(self) -> bool:
        """Starts acquisition from active source."""
        with self._lock:
            if not self.active_source:
                return False
            res = self.active_source.start()
            if res:
                self.status_changed.emit(f"STREAMING ({self.active_source.source_name})")
            return res

    def stop(self) -> bool:
        """Stops active acquisition and clears buffer."""
        with self._lock:
            if not self.active_source:
                return True
            res = self.active_source.stop()
            self.signal_buffer.clear()
            self.status_changed.emit("STOPPED")
            return res

    def pause(self) -> bool:
        """Pauses active acquisition."""
        with self._lock:
            if not self.active_source:
                return False
            res = self.active_source.pause()
            if res:
                self.status_changed.emit("PAUSED")
            return res

    def resume(self) -> bool:
        """Resumes active acquisition."""
        with self._lock:
            if not self.active_source:
                return False
            res = self.active_source.resume()
            if res:
                self.status_changed.emit("STREAMING")
            return res

    def status(self) -> str:
        with self._lock:
            return self.active_source.status() if self.active_source else "IDLE"

    def _on_frame(self, frame: SignalFrame):
        """Internal Qt signal handler for incoming SignalFrame payloads."""
        self._process_incoming_frame(frame)

    def _on_frame_cb(self, frame: SignalFrame):
        """Internal callback handler for incoming SignalFrame payloads."""
        pass  # Handled via _on_frame to prevent double ingestion

    def _process_incoming_frame(self, frame: SignalFrame):
        """Validates, tracks telemetry, and routes SignalFrame into BoundedSignalBuffer."""
        if not isinstance(frame, SignalFrame):
            return

        with self._lock:
            self._frames_received += 1
            self._samples_received += frame.num_samples

            if self._last_sequence >= 0 and frame.sequence > self._last_sequence + frame.num_samples:
                gap = frame.sequence - (self._last_sequence + frame.num_samples)
                self._sequence_gaps += gap
            self._last_sequence = frame.sequence

        self.signal_buffer.append_frame(frame)
        self.frame_received.emit(frame)
