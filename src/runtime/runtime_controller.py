"""
Application Runtime Controller for NeuroSim 2.0 (Phase 2A)
Orchestrates AcquisitionManager, BoundedSignalBuffer, PSDAnalyzer, SessionModel, RuleBasedClassifier, and DatabaseManager.
Exposes UI-neutral runtime capabilities, controlled analysis cadence, and zero-input safety.
"""

import time
import threading
from typing import Tuple, Dict, Optional, Any
from PySide6.QtCore import QObject, Signal

from src.core.enums import SignalSourceType
from src.core.signal_contract import SignalFrame
from src.processing.signal_buffer import BoundedSignalBuffer
from src.acquisition.synthetic_source import SyntheticSignalSource
from src.acquisition.acquisition_manager import AcquisitionManager
from src.processing.psd import PSDAnalyzer
from src.features.extractor import EEGFeatureExtractor
from src.classification.rule_classifier import RuleBasedClassifier
from src.database.db_manager import DatabaseManager
from src.analysis.research_engine import ResearchAnalyticsEngine
from src.runtime.session_model import SessionModel, SessionState

from src.utils.logger import get_logger

class RuntimeController(QObject):
    """
    Core Application Runtime Controller for NeuroSim 2.0.
    Manages session lifecycle, signal routing, quantitative analysis cadence, and runtime telemetry.
    """
    analysis_updated = Signal(dict) # Emits latest analysis dictionary
    session_state_changed = Signal(str) # Emits state name
    runtime_error_occurred = Signal(str) # Emits error string

    def __init__(self, buffer_capacity: int = 1250, sampling_rate: int = 250, channels: Tuple[str, ...] = ("Ch1",), parent=None):
        super().__init__(parent)
        self.sampling_rate = sampling_rate
        self.channels = tuple(channels)
        self.logger = get_logger("runtime")

        # Core Subsystems
        self.signal_buffer = BoundedSignalBuffer(capacity=buffer_capacity, sampling_rate=sampling_rate, channels=self.channels)
        self.acq_mgr = AcquisitionManager(self.signal_buffer)
        self.psd_analyzer = PSDAnalyzer(sampling_rate=sampling_rate)
        self.feature_extractor = EEGFeatureExtractor()
        self.classifier = RuleBasedClassifier()
        self.db_manager = DatabaseManager()
        self.research_engine = ResearchAnalyticsEngine(db_manager=self.db_manager)

        # Register official Synthetic Source
        self.synthetic_source = SyntheticSignalSource(sampling_rate=sampling_rate, channels=self.channels)
        self.acq_mgr.register_source("synthetic", self.synthetic_source)

        # Connect internal frame signal and callback for cadence tracking
        try:
            self.acq_mgr.frame_received.connect(self._on_frame_received)
        except (RuntimeError, AttributeError):
            pass
        self.acq_mgr.add_callback(self._on_frame_received)

        # Session & Cadence Management
        self.current_session: Optional[SessionModel] = None
        self._lock = threading.RLock()

        self._analysis_interval_sec = 0.2  # 200 ms cadence
        self._last_analysis_time = 0.0
        self._latest_analysis_result: Optional[Dict[str, Any]] = None
        self._last_error = ""

    # ------------------------------------------------------------------
    # Zero-Input & Runtime Status
    # ------------------------------------------------------------------

    def is_idle(self) -> bool:
        """Returns True if runtime is idle with zero active recording."""
        with self._lock:
            return self.current_session is None or self.current_session.state == SessionState.IDLE

    def get_runtime_status(self) -> Dict[str, Any]:
        """Returns a thread-safe UI-neutral dictionary of current runtime state."""
        with self._lock:
            state_str = self.current_session.state.name if self.current_session else "IDLE"
            duration = self.current_session.update_duration() if self.current_session else 0.0
            samples_rec = self.acq_mgr.samples_received
            frames_rec = self.acq_mgr.frames_received
            seq_gaps = self.acq_mgr.sequence_gaps
            source_name = self.acq_mgr.active_source.source_name if self.acq_mgr.active_source else "NONE"
            buffer_count = len(self.signal_buffer)

            return {
                "state": state_str,
                "session_active": self.current_session is not None and self.current_session.state == SessionState.RECORDING,
                "session_id": self.current_session.session_id if self.current_session else None,
                "duration_sec": duration,
                "source_name": source_name,
                "sampling_rate": self.sampling_rate,
                "channels": list(self.channels),
                "samples_received": samples_rec,
                "frames_received": frames_rec,
                "sequence_gaps": seq_gaps,
                "buffer_count": buffer_count,
                "has_latest_analysis": self._latest_analysis_result is not None,
                "metrics": self._latest_analysis_result["metrics"] if self._latest_analysis_result else None,
                "classification": self._latest_analysis_result.get("classification") if self._latest_analysis_result else None,
                "last_error": self._last_error
            }

    def get_latest_analysis(self) -> Optional[Dict[str, Any]]:
        """Returns latest quantitative analysis result dictionary or None."""
        with self._lock:
            return dict(self._latest_analysis_result) if self._latest_analysis_result else None

    def get_session_model(self) -> Optional[SessionModel]:
        """Returns current session model or None."""
        with self._lock:
            return self.current_session

    # ------------------------------------------------------------------
    # Session & Simulator Lifecycle Controls
    # ------------------------------------------------------------------

    def select_source(self, source_name: str) -> bool:
        """Selects acquisition source by name."""
        with self._lock:
            return self.acq_mgr.select_source(source_name)

    def start_simulator(self, seed: Optional[int] = None) -> SessionModel:
        """Convenience method to explicitly start Synthetic Simulator mode."""
        with self._lock:
            if seed is not None:
                self.synthetic_source.set_seed(seed)
            self.select_source("synthetic")
            return self.start_session(source_name="synthetic")

    def stop_simulator(self) -> bool:
        """Convenience method to stop Synthetic Simulator mode."""
        with self._lock:
            res = self.stop_session()
            return res is not None

    def start_session(self, source_name: str = "synthetic") -> SessionModel:
        """Starts a new recording session with specified source."""
        with self._lock:
            if self.current_session and self.current_session.state in (SessionState.RECORDING, SessionState.PAUSED):
                self.stop_session()

            # Bind source
            if not self.select_source(source_name):
                err = f"Failed to select source '{source_name}'"
                self._last_error = err
                self.runtime_error_occurred.emit(err)
                raise ValueError(err)

            # Clear buffer and reset telemetry
            self.signal_buffer.clear()
            self.acq_mgr.reset_telemetry()
            self._latest_analysis_result = None
            self._last_error = ""

            source_obj = self.acq_mgr.active_source
            s_type = source_obj.source_type if source_obj else SignalSourceType.UNKNOWN

            session = SessionModel(
                source_name=source_name,
                source_type=s_type,
                sampling_rate=self.sampling_rate,
                channels=self.channels,
                state=SessionState.RECORDING
            )
            self.current_session = session

            # Start underlying source
            if not self.acq_mgr.start():
                session.state = SessionState.ERROR
                session.last_error = "Acquisition start failed"
                self.session_state_changed.emit("ERROR")
                raise RuntimeError("Failed to start acquisition manager")

            self.session_state_changed.emit("RECORDING")
            self.logger.info(f"Started session '{session.session_id}' using source '{source_name}'")
            return session

    def stop_session(self) -> Optional[SessionModel]:
        """Stops active recording session, halts acquisition, persists session record to DB, clears live state."""
        with self._lock:
            if not self.current_session or self.current_session.state in (SessionState.IDLE, SessionState.STOPPED):
                return self.current_session

            # Perform final analysis tick if needed before stopping
            if not self._latest_analysis_result and len(self.signal_buffer) >= 32:
                self.run_analysis_tick()

            self.acq_mgr.stop()
            self.current_session.samples_received = self.acq_mgr.samples_received
            self.current_session.frames_received = self.acq_mgr.frames_received
            self.current_session.latest_analysis = self._latest_analysis_result
            self.current_session.stop_session()

            # Save session to DatabaseManager
            if self._latest_analysis_result and self.current_session.samples_received > 0:
                m = self._latest_analysis_result["metrics"]
                cls = self._latest_analysis_result.get("classification", {})
                self.db_manager.save_session({
                    "session_id": self.current_session.session_id,
                    "duration": self.current_session.duration_sec,
                    "sampling_rate": self.sampling_rate,
                    "mode": self.current_session.source_name.upper(),
                    "rel_delta": m.get("delta_rel", 25.0),
                    "rel_theta": m.get("theta_rel", 25.0),
                    "rel_alpha": m.get("alpha_rel", 25.0),
                    "rel_beta": m.get("beta_rel", 25.0),
                    "dominant_band": m.get("dominant_band", "ALPHA"),
                    "cognitive_state": cls.get("cognitive_state", "MODERATE"),
                    "stress_index": m.get("stress_index", 0.5),
                    "confidence": cls.get("confidence", 85.0),
                    "notes": f"Session recorded via {self.current_session.source_name}"
                })

            finished_session = self.current_session
            self.session_state_changed.emit("STOPPED")
            self.logger.info(f"Stopped session '{finished_session.session_id}'. Duration: {finished_session.duration_sec:.2f}s, Samples: {finished_session.samples_received}")
            return finished_session

    def pause_session(self) -> bool:
        """Pauses active recording session."""
        with self._lock:
            if not self.current_session or self.current_session.state != SessionState.RECORDING:
                return False
            res = self.acq_mgr.pause()
            if res:
                self.current_session.pause_session()
                self.session_state_changed.emit("PAUSED")
            return res

    def resume_session(self) -> bool:
        """Resumes active recording session from paused state."""
        with self._lock:
            if not self.current_session or self.current_session.state != SessionState.PAUSED:
                return False
            res = self.acq_mgr.resume()
            if res:
                self.current_session.resume_session()
                self.session_state_changed.emit("RECORDING")
            return res

    # ------------------------------------------------------------------
    # Signal Frame Handler & Controlled Analysis Cadence
    # ------------------------------------------------------------------

    def _on_frame_received(self, frame: SignalFrame):
        """Triggered on incoming SignalFrame. Evaluates analysis cadence."""
        with self._lock:
            if not self.current_session or self.current_session.state != SessionState.RECORDING:
                return

            self.current_session.samples_received += frame.num_samples
            self.current_session.frames_received += 1
            self.current_session.update_duration()

            now = time.time()
            if now - self._last_analysis_time >= self._analysis_interval_sec:
                self.run_analysis_tick()
                self._last_analysis_time = now

    def run_analysis_tick(self) -> Optional[Dict[str, Any]]:
        """
        Executes a quantitative analysis tick on thread-safe buffer snapshot.
        Gracefully handles insufficient samples (< 32) without generating fake metrics.
        """
        with self._lock:
            snap = self.signal_buffer.snapshot()
            sample_count = snap["count"]

            if sample_count < 32:
                # Insufficient samples for Welch PSD estimate
                return None

            try:
                primary_samples = snap["samples"]
                freqs, psd = self.psd_analyzer.compute_psd(primary_samples)
                combined_metrics = self.psd_analyzer.analyze_bands(freqs, psd)
                combined_metrics["total_power"] = float(
                    sum(combined_metrics.get(f"{band}_abs", 0.0) for band in ("delta", "theta", "alpha", "beta"))
                )

                psd_metrics_for_extractor = {
                    'rel_powers': {
                        'delta': combined_metrics.get('delta_rel', 0.0),
                        'theta': combined_metrics.get('theta_rel', 0.0),
                        'alpha': combined_metrics.get('alpha_rel', 0.0),
                        'beta': combined_metrics.get('beta_rel', 0.0),
                    },
                    'theta_beta_ratio': combined_metrics.get('tbr', 1.0),
                    'alpha_beta_ratio': combined_metrics.get('abr', 1.0),
                    'stress_index': combined_metrics.get('stress_index', 0.5),
                    'total_power': float(sum(combined_metrics.get(f"{b}_abs", 0.0) for b in ('delta', 'theta', 'alpha', 'beta')))
                }
                features = self.feature_extractor.extract_features(psd_metrics_for_extractor)
                classification = self.classifier.classify(psd_metrics_for_extractor)

                # Quality evaluation across all channels
                from src.processing.quality import EEGQualityEvaluator
                quality_evaluator = EEGQualityEvaluator(sampling_rate=self.sampling_rate)
                all_samples_arr = snap.get("all_samples", primary_samples.reshape(1, -1))
                quality_info = quality_evaluator.evaluate_multichannel(all_samples_arr, self.channels, freqs, psd)

                combined_metrics["quality_score"] = quality_info.get("overall_score")
                combined_metrics["quality_rating"] = quality_info.get("overall_rating")
                combined_metrics["usable_data_pct"] = quality_info.get("overall_usable_pct", 100.0)
                combined_metrics["artifact_burden_pct"] = quality_info.get("overall_artifact_pct", 0.0)

                analysis_result = {
                    "timestamp": time.time(),
                    "sample_count": sample_count,
                    "duration_sec": snap["duration_sec"],
                    "metrics": combined_metrics,
                    "quality": quality_info,
                    "classification": classification,
                    "features": features,
                    "feature_names": self.feature_extractor.feature_names(),
                    "spectrum": {
                        "frequencies_hz": [float(value) for value in freqs],
                        "power": [float(value) for value in psd],
                    }
                }

                self._latest_analysis_result = analysis_result
                if self.current_session:
                    self.current_session.latest_analysis = analysis_result

                self.analysis_updated.emit(analysis_result)
                return analysis_result

            except Exception as e:
                self._last_error = f"Analysis error: {str(e)}"
                self.runtime_error_occurred.emit(self._last_error)
                return None

# Alias for Phase 2A product runtime foundation
NeuroSimRuntime = RuntimeController
