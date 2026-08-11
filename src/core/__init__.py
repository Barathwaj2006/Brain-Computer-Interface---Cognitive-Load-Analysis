"""
NeuroSim 2.0 Core Package (Phase 1A)
Exposes canonical signal frame contract and source enums.
"""

from src.core.enums import SignalSourceType
from src.core.signal_contract import SignalFrame

__all__ = [
    "SignalSourceType",
    "SignalFrame"
]
