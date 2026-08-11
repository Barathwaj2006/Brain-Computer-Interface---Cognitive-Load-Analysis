"""Thin HTTP-facing adapter over the authoritative NeuroSim runtime."""

from __future__ import annotations

from typing import Any, Dict, Optional, List

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
        classification = analysis.get("classification") if analysis else None
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
            "classification": classification,
            "cognitive_state": classification.get("cognitive_state") if classification else None,
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

    def history(self) -> List[Dict[str, Any]]:
        """Returns all recorded sessions from SQLite DatabaseManager."""
        return self.runtime.db_manager.get_all_sessions()

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

    def report_data(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Builds report data for PDF export for current session or historical session_id."""
        if session_id:
            db_rec = self.runtime.db_manager.get_session_by_id(session_id)
            if not db_rec:
                raise RuntimeError(f"Session '{session_id}' not found in database archive.")
            return {
                "session_id": db_rec["session_id"],
                "duration_sec": db_rec["duration"],
                "source_name": db_rec["mode"],
                "sample_count": int(db_rec["duration"] * db_rec["sampling_rate"]),
                "frame_count": int(db_rec["duration"] * db_rec["sampling_rate"] / 25),
                "channels": list(self.runtime.channels),
                "cognitive_state": db_rec["cognitive_state"],
                "delta_abs": 0.0,
                "theta_abs": 0.0,
                "alpha_abs": 0.0,
                "beta_abs": 0.0,
                "delta_rel": db_rec["rel_delta"],
                "theta_rel": db_rec["rel_theta"],
                "alpha_rel": db_rec["rel_alpha"],
                "beta_rel": db_rec["rel_beta"],
                "total_power": 1.0,
                "dominant_frequency": 10.0,
                "dominant_band": db_rec["dominant_band"],
                "tbr": 1.0,
                "abr": 1.0,
                "stress_index": db_rec["stress_index"],
            }

        session = self.runtime.get_session_model()
        latest_analysis = (session.latest_analysis if session else None) or self.runtime.get_latest_analysis()
        
        # Fallback to database archive if available
        if not latest_analysis:
            history = self.runtime.db_manager.get_all_sessions()
            if history:
                return self.report_data(session_id=history[0]["session_id"])
            raise RuntimeError("A completed analysis or saved session is required for report export.")

        session_id = session.session_id if session else "SESSION_CURRENT"
        duration_sec = session.duration_sec if session else 0.0
        source_name = session.source_name if session else "synthetic"
        sample_count = session.samples_received if session else 0
        frame_count = session.frames_received if session else 0

        metrics = latest_analysis["metrics"]
        classification = latest_analysis.get("classification", {})
        return {
            "session_id": session_id,
            "duration_sec": duration_sec,
            "source_name": source_name,
            "sample_count": sample_count,
            "frame_count": frame_count,
            "channels": list(self.runtime.channels),
            "cognitive_state": classification.get("cognitive_state", "MODERATE"),
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
