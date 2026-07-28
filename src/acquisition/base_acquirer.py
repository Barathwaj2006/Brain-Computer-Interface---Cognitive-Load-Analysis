"""
Base Data Acquisition Interface
Standardizes streaming data sources for both Simulation Mode and Hardware Mode.
"""

import numpy as np
from typing import Tuple, Dict, Optional
from PySide6.QtCore import QObject, Signal

class BaseAcquirer(QObject):
    data_received = Signal(np.ndarray, dict)  # (waveform_chunk, info_dict)
    status_changed = Signal(str, bool)       # (status_message, is_connected)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_running = False

    def start_acquisition(self):
        self.is_running = True

    def stop_acquisition(self):
        self.is_running = False
