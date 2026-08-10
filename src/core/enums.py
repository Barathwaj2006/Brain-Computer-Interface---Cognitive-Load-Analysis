"""
Canonical Signal Source Types for NeuroSim 2.0 (Phase 1A)
Defines transport and signal origin identifiers.
"""

from enum import Enum, auto

class SignalSourceType(Enum):
    """Generic source type identifiers for NeuroSim 2.0."""
    SIMULATOR = auto()
    ESP32_USB = auto()
    ESP32_WIFI = auto()
    EEG_HARDWARE = auto()
    UNKNOWN = auto()

    @classmethod
    def from_str(cls, val: str) -> "SignalSourceType":
        """Parses string identifier into SignalSourceType enum."""
        if not val:
            return cls.UNKNOWN
        clean = str(val).strip().upper()
        for item in cls:
            if item.name == clean:
                return item
        return cls.UNKNOWN
