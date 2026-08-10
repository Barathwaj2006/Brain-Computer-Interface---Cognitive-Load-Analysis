"""
Lightweight In-Memory Session Model for NeuroSim 2.0 (Phase 2A)
Encapsulates runtime session metadata, timing, state, sample counts, and latest quantitative metrics.
"""

import time
import uuid
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Tuple, Dict, Optional, Any
from src.core.enums import SignalSourceType

class SessionState(Enum):
    """Runtime Session Lifecycle States."""
    IDLE = auto()
    PREPARING = auto()
    RECORDING = auto()
    PAUSED = auto()
    STOPPED = auto()
    ERROR = auto()

@dataclass
class SessionModel:
    """
    Lightweight In-Memory Session Model.
    Tracks session timing, source configuration, sample counts, and latest analysis results.
    """
    session_id: str = field(default_factory=lambda: f"SES-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4].upper()}")
    start_timestamp: float = field(default_factory=time.time)
    end_timestamp: Optional[float] = None
    duration_sec: float = 0.0
    source_name: str = "NONE"
    source_type: SignalSourceType = SignalSourceType.UNKNOWN
    sampling_rate: int = 250
    channels: Tuple[str, ...] = ("Ch1",)
    samples_received: int = 0
    frames_received: int = 0
    state: SessionState = SessionState.IDLE
    latest_analysis: Optional[Dict[str, Any]] = None
    last_error: str = ""

    def update_duration(self) -> float:
        """Updates and returns elapsed duration in seconds."""
        if self.state in (SessionState.RECORDING, SessionState.PAUSED):
            self.duration_sec = max(0.0, round(time.time() - self.start_timestamp, 2))
        elif self.end_timestamp is not None:
            self.duration_sec = max(0.0, round(self.end_timestamp - self.start_timestamp, 2))
        return self.duration_sec

    def stop_session(self):
        """Finalizes session timestamps and sets state to STOPPED."""
        self.end_timestamp = time.time()
        self.update_duration()
        self.state = SessionState.STOPPED

    def to_dict(self) -> Dict[str, Any]:
        """Returns dictionary representation of session state."""
        return {
            "session_id": self.session_id,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "duration_sec": self.update_duration(),
            "source_name": self.source_name,
            "source_type": self.source_type.name,
            "sampling_rate": self.sampling_rate,
            "channels": list(self.channels),
            "samples_received": self.samples_received,
            "frames_received": self.frames_received,
            "state": self.state.name,
            "latest_analysis": self.latest_analysis,
            "last_error": self.last_error
        }
