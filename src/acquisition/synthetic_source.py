"""
SyntheticSignalSource Module for NeuroSim 2.0 (Phase 2 Acquisition Core)
Wraps existing SyntheticEEGGenerator inside generic BaseSignalSource abstraction.
Generates deterministic SignalFrames with monotonically increasing sequence numbers and timestamps.
"""

import time
import threading
from typing import Optional, Dict
from src.app.state import InputSource
from src.acquisition.contracts import BaseSignalSource, SignalFrame
from src.simulation.eeg_generator import SyntheticEEGGenerator

class SyntheticSignalSource(BaseSignalSource):
    """
    Synthetic EEG Signal Source implementing BaseSignalSource.
    Wraps mathematical SyntheticEEGGenerator and streams SignalFrame objects.
    """

    def __init__(self, sampling_rate: int = 250, seed: Optional[int] = None, parent=None):
        super().__init__(source_name="SyntheticSource", parent=parent)
        self.sampling_rate = sampling_rate
        self.seed = seed
        if seed is not None:
            import numpy as np
            np.random.seed(seed)

        self.generator = SyntheticEEGGenerator(sampling_rate=self.sampling_rate)
        self._sequence = 0
        self._lock = threading.Lock()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def set_seed(self, seed: int):
        """Sets numpy random seed for deterministic generation."""
        import numpy as np
        self.seed = seed
        np.random.seed(seed)

    def set_amplitudes(self, delta: float, theta: float, alpha: float, beta: float):
        """Passes target wave amplitudes to underlying generator."""
        self.generator.set_amplitudes(delta, theta, alpha, beta)

    def set_noise(self, noise_level: float):
        """Passes noise level setting to underlying generator."""
        self.generator.set_noise(noise_level)

    def start(self) -> bool:
        """Starts background generator streaming thread."""
        with self._lock:
            if self._running:
                return True
            self._running = True
            self._paused = False
            self._stop_event.clear()
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()
            self.state_changed.emit("RUNNING")
            return True

    def stop(self) -> bool:
        """Stops background generator streaming thread."""
        with self._lock:
            if not self._running:
                return True
            self._running = False
            self._paused = False
            self._stop_event.set()

        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
        self._worker_thread = None
        self.state_changed.emit("STOPPED")
        return True

    def pause(self) -> bool:
        """Pauses frame generation without stopping background worker."""
        with self._lock:
            if not self._running:
                return False
            self._paused = True
            self.state_changed.emit("PAUSED")
            return True

    def resume(self) -> bool:
        """Resumes frame generation from paused state."""
        with self._lock:
            if not self._running:
                return False
            self._paused = False
            self.state_changed.emit("RUNNING")
            return True

    def generate_frame(self, num_samples: int = 10) -> SignalFrame:
        """Manually produces and returns a single SignalFrame payload."""
        t_now = time.time()
        waveform, meta = self.generator.generate_chunk(num_samples=num_samples)

        with self._lock:
            seq = self._sequence
            self._sequence += num_samples

        frame = SignalFrame(
            timestamp=t_now,
            sequence=seq,
            sampling_rate=self.sampling_rate,
            channel_count=1,
            channels=["Ch1"],
            data=[float(x) for x in waveform],
            source=InputSource.SIMULATOR,
            metadata={"source": "synthetic", "generator": "SyntheticEEGGenerator", "amplitudes": meta},
            transport="Internal Synthetic",
            device_id="Synthetic Generator",
            integrity_status="VALID"
        )
        return frame

    def _worker_loop(self):
        """Background streaming worker emitting frames at 250 Hz timing intervals."""
        chunk_size = 10  # 40 ms chunks @ 250 Hz
        interval = chunk_size / self.sampling_rate  # 0.040s

        while not self._stop_event.is_set():
            t_start = time.time()
            if self._running and not self._paused:
                frame = self.generate_frame(num_samples=chunk_size)
                try:
                    self.emit_frame(frame)
                except (RuntimeError, AttributeError):
                    break

            elapsed = time.time() - t_start
            sleep_time = max(0.001, interval - elapsed)
            time.sleep(sleep_time)
