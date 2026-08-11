"""
Synthetic Signal Source Module for NeuroSim 2.0 (Phase 1C)
Wraps mathematical SyntheticEEGGenerator in generic BaseSignalSource abstraction.
Generates real single-channel and multi-channel numerical SignalFrames at 250 Hz with deterministic seed control.
"""

import time
import threading
from typing import Tuple, Dict, Optional, Any, List
import numpy as np
from src.core.enums import SignalSourceType
from src.core.signal_contract import SignalFrame
from src.acquisition.base_acquirer import BaseSignalSource
from src.simulation.eeg_generator import SyntheticEEGGenerator

class SyntheticSignalSource(BaseSignalSource):
    """
    Synthetic EEG Signal Source implementing BaseSignalSource.
    Generates single-channel or multi-channel canonical SignalFrames using SyntheticEEGGenerator.
    """

    def __init__(self, sampling_rate: int = 250, channels: Tuple[str, ...] = ("Ch1",), seed: Optional[int] = None, parent=None):
        super().__init__(source_type=SignalSourceType.SIMULATOR, source_name="SyntheticSource", parent=parent)
        self.sampling_rate = sampling_rate
        self.channels = tuple(channels) if channels else ("Ch1",)
        self.channel_count = len(self.channels)
        self.seed = seed

        # Create generator instances per channel for realistic multi-channel EEG synthesis
        self._generators: List[SyntheticEEGGenerator] = [
            SyntheticEEGGenerator(sampling_rate=self.sampling_rate) for _ in range(self.channel_count)
        ]
        
        self._sequence = 0
        self._lock = threading.RLock()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        if seed is not None:
            self.set_seed(seed)

    def set_seed(self, seed: int):
        """Sets numpy random seed and resets generators for deterministic generation across all channels."""
        with self._lock:
            self.seed = seed
            np.random.seed(seed)
            self._sequence = 0
            self._generators = [
                SyntheticEEGGenerator(sampling_rate=self.sampling_rate) for _ in range(self.channel_count)
            ]

    def set_amplitudes(self, delta: float, theta: float, alpha: float, beta: float, channel_idx: Optional[int] = None):
        """Updates wave amplitudes for specific channel or all channels."""
        with self._lock:
            if channel_idx is not None and 0 <= channel_idx < self.channel_count:
                self._generators[channel_idx].set_amplitudes(delta, theta, alpha, beta)
            else:
                for gen in self._generators:
                    gen.set_amplitudes(delta, theta, alpha, beta)

    def set_noise(self, noise_level: float):
        """Updates noise level across all channels."""
        with self._lock:
            for gen in self._generators:
                gen.set_noise(noise_level)

    def generate_frame(self, num_samples: int = 10) -> SignalFrame:
        """
        Manually produces and returns a single canonical SignalFrame payload.
        Ensures multi-channel temporal alignment.
        """
        t_now = time.time()
        ch_waveforms = []
        ch_meta = {}

        with self._lock:
            for idx, gen in enumerate(self._generators):
                w, m = gen.generate_chunk(num_samples=num_samples)
                ch_waveforms.append(tuple(float(x) for x in w))
                ch_meta[self.channels[idx]] = m

            seq = self._sequence
            self._sequence += num_samples

        frame = SignalFrame(
            timestamp=t_now,
            sequence=seq,
            sampling_rate=self.sampling_rate,
            channel_count=self.channel_count,
            channels=self.channels,
            data=tuple(ch_waveforms),
            source=SignalSourceType.SIMULATOR,
            metadata={
                "source": "synthetic",
                "generator": "SyntheticEEGGenerator",
                "channel_amplitudes": ch_meta
            }
        )
        return frame

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
            self.status_changed.emit("STREAMING", True)
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
        self.status_changed.emit("STOPPED", False)
        return True

    def pause(self) -> bool:
        """Pauses frame generation without stopping background worker."""
        with self._lock:
            if not self._running:
                return False
            self._paused = True
            self.status_changed.emit("PAUSED", True)
            return True

    def resume(self) -> bool:
        """Resumes frame generation from paused state."""
        with self._lock:
            if not self._running:
                return False
            self._paused = False
            self.status_changed.emit("STREAMING", True)
            return True

    def _worker_loop(self):
        """Background streaming worker emitting frames at 250 Hz timing intervals."""
        chunk_size = 10  # 40 ms chunks @ 250 Hz
        interval = chunk_size / self.sampling_rate  # 0.040s

        while not self._stop_event.is_set():
            t_start = time.time()
            if self._running and not self._paused:
                try:
                    frame = self.generate_frame(num_samples=chunk_size)
                    self.emit_frame(frame)
                except Exception as e:
                    print(f"[SyntheticSource Worker Exception] {e}")
                    break

            elapsed = time.time() - t_start
            sleep_time = max(0.001, interval - elapsed)
            time.sleep(sleep_time)
