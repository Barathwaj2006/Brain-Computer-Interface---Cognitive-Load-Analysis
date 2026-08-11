"""Thin HTTP-facing adapter over the authoritative NeuroSim runtime."""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.runtime.runtime_controller import RuntimeController
from src.runtime.session_model import SessionState


class RuntimeService:
    """Expose RuntimeController data without maintaining a second runtime state."""

    def __init__(self, runtime: Optional[RuntimeController] = None):
        self.runtime = runtime or RuntimeController(
            sampling_rate=250,
            channels=("FP1", "FP2", "O1", "O2"),
        )

    def state(self) -> Dict[str, Any]:
        status = self.runtime.get_runtime_status()
        analysis = self.runtime.get_latest_analysis()
        return {
            "state": status["state"],
            "streaming": status["state"] == SessionState.RECORDING.name,
            "paused": status["state"] == SessionState.PAUSED.name,
            "session_id": status["session_id"],
            "duration_sec": status["duration_sec"],
            "source": status["source_name"],
            "samples": status["samples_received"],
            "frames": status["frames_received"],
            "sequence_gaps": status["sequence_gaps"],
            "buffer_count": status["buffer_count"],
            "channels": status["channels"],
            "analysis_available": analysis is not None,
            "metrics": analysis["metrics"] if analysis else None,
            "hardware": {"connected": False, "status": "NOT_CONNECTED"},
            "last_error": status["last_error"] or None,
        }

    def waveform(self, seconds: float = 5.0) -> Dict[str, Any]:
        if seconds not in (1.0, 2.0, 5.0):
            raise ValueError("seconds must be one of: 1, 2, 5")
        samples, timestamps, sequences = self.runtime.signal_buffer.get_window(seconds)
        channels = self.runtime.signal_buffer.channels
        return {
            "seconds": seconds,
            "channels": {channel: samples[index].tolist() for index, channel in enumerate(channels)},
            "timestamps": timestamps.tolist(),
            "sequences": sequences.tolist(),
        }

    def analysis(self) -> Optional[Dict[str, Any]]:
        return self.runtime.get_latest_analysis()

    def start(self) -> Dict[str, Any]:
        self.runtime.start_simulator()
        return self.state()

    def pause(self) -> Dict[str, Any]:
        if not self.runtime.pause_session():
            raise RuntimeError("Cannot pause: runtime is not recording")
        return self.state()

    def resume(self) -> Dict[str, Any]:
        if not self.runtime.resume_session():
            raise RuntimeError("Cannot resume: runtime is not paused")
        return self.state()

    def stop(self) -> Dict[str, Any]:
        session = self.runtime.stop_session()
        if session is None:
            raise RuntimeError("Cannot stop: no session exists")
        return self.state()

    def report_data(self) -> Dict[str, Any]:
        session = self.runtime.get_session_model()
        if not session or session.state != SessionState.STOPPED or not session.latest_analysis:
            raise RuntimeError("A stopped session with completed analysis is required for report export")

        metrics = session.latest_analysis["metrics"]
        return {
            "session_id": session.session_id,
            "duration_sec": session.duration_sec,
            "source_name": session.source_name,
            "sample_count": session.samples_received,
            "frame_count": session.frames_received,
            "channels": list(session.channels),
            "cognitive_state": None,
            "delta_abs": metrics.get("delta_abs"),
            "theta_abs": metrics.get("theta_abs"),
            "alpha_abs": metrics.get("alpha_abs"),
            "beta_abs": metrics.get("beta_abs"),
            "delta_rel": metrics.get("delta_rel"),
            "theta_rel": metrics.get("theta_rel"),
            "alpha_rel": metrics.get("alpha_rel"),
            "beta_rel": metrics.get("beta_rel"),
            "total_power": metrics.get("total_power"),
            "dominant_frequency": metrics.get("dominant_frequency"),
            "dominant_band": metrics.get("dominant_band"),
            "tbr": metrics.get("tbr"),
            "abr": metrics.get("abr"),
            "stress_index": metrics.get("stress_index"),
        }
