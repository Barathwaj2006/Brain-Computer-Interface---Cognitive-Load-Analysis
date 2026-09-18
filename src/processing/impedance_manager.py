"""
=================================================================================
NEUROSIM : ELECTRODE IMPEDANCE & QUALITY ASSURANCE ENGINE
Conforms to:
- IEC 60601-2-26 continuous impedance monitoring (< 5 kOhm standard)
- Automatic Lead-Off detection and pre-flight recording interlocks
=================================================================================
"""

import time
import random
from typing import Dict, Any, Tuple

class ImpedanceManager:
    """
    Tracks and validates continuous electrode-skin contact impedances across
    standard 10-20 positions.
    """
    ELECTRODES = ["Fp1", "Fp2", "C3", "C4", "P3", "P4", "O1", "O2", "Ref", "DRL"]
    THRESHOLD_OPTIMAL = 5.0     # < 5.0 kOhm = Green
    THRESHOLD_ACCEPTABLE = 10.0 # 5.0 - 10.0 kOhm = Yellow; > 10 kOhm = Red (Lead Off)

    def __init__(self):
        # Default starting values in optimal clinical range (2.0 - 4.5 kOhm)
        self.impedances: Dict[str, float] = {
            el: round(2.5 + random.uniform(-0.5, 1.0), 2) for el in self.ELECTRODES
        }
        self.last_update = time.time()
        self.override_active = False
        self.override_reason = ""
        self.override_timestamp = 0.0

    def update_channel(self, channel: str, value_kohm: float):
        if channel in self.impedances:
            self.impedances[channel] = max(0.1, round(float(value_kohm), 2))
            self.last_update = time.time()

    def update_all(self, values: Dict[str, float]):
        for k, v in values.items():
            if k in self.impedances:
                self.impedances[k] = max(0.1, round(float(v), 2))
        self.last_update = time.time()

    def get_status(self, channel: str) -> str:
        val = self.impedances.get(channel, 999.0)
        if val < self.THRESHOLD_OPTIMAL:
            return "OPTIMAL"
        elif val <= self.THRESHOLD_ACCEPTABLE:
            return "ACCEPTABLE"
        return "LEAD_OFF"

    def is_preflight_passed(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validates if all electrodes satisfy the < 5.0 kOhm requirement.
        Returns (passed, details).
        """
        failing_channels = {}
        for el, val in self.impedances.items():
            if val >= self.THRESHOLD_OPTIMAL:
                failing_channels[el] = {
                    "impedance_kohm": val,
                    "status": self.get_status(el)
                }

        passed = len(failing_channels) == 0
        return passed, {
            "passed": passed,
            "can_record": passed or self.override_active,
            "override_active": self.override_active,
            "override_reason": self.override_reason,
            "threshold_optimal_kohm": self.THRESHOLD_OPTIMAL,
            "threshold_acceptable_kohm": self.THRESHOLD_ACCEPTABLE,
            "failing_channels": failing_channels,
            "all_channels": {
                el: {
                    "kohm": self.impedances[el],
                    "status": self.get_status(el)
                } for el in self.ELECTRODES
            }
        }

    def set_clinical_override(self, reason: str) -> Dict[str, Any]:
        """Physician authorized clinical recording override."""
        self.override_active = True
        self.override_reason = reason.strip() or "Physician Authorized Clinical Protocol Override"
        self.override_timestamp = time.time()
        return {
            "override_active": True,
            "reason": self.override_reason,
            "timestamp": self.override_timestamp
        }

    def clear_clinical_override(self):
        self.override_active = False
        self.override_reason = ""
        self.override_timestamp = 0.0

    def simulate_gel_settling(self):
        """Simulates physiological electrode-gel stabilization."""
        for el in self.ELECTRODES:
            cur = self.impedances[el]
            # Drift toward 2.5 kOhm
            drift = (2.5 - cur) * 0.15 + random.uniform(-0.1, 0.1)
            self.impedances[el] = max(0.8, round(cur + drift, 2))
        self.last_update = time.time()
