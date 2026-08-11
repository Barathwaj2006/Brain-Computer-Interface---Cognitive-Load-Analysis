"""
Phase 2A Product Runtime Foundation Test Suite for NeuroSim 2.0
Validates RuntimeController orchestration, SessionModel tracking, zero-input safety,
explicit simulator control, controlled analysis cadence, and error handling.
"""

import unittest
import time
import numpy as np
from PySide6.QtWidgets import QApplication

from src.core.enums import SignalSourceType
from src.runtime.session_model import SessionModel, SessionState
from src.runtime.runtime_controller import RuntimeController, NeuroSimRuntime

app = QApplication.instance() or QApplication([])

class TestRuntimeFoundation(unittest.TestCase):

    def setUp(self):
        self.runtime = RuntimeController(buffer_capacity=1250, sampling_rate=250, channels=("Ch1",))

    def tearDown(self):
        self.runtime.stop_session()

    def test_01_startup_idle_state(self):
        """1. Startup idle state: no active session, zero samples, zero metrics."""
        status = self.runtime.get_runtime_status()
        self.assertEqual(status["state"], "IDLE")
        self.assertFalse(status["session_active"])
        self.assertIsNone(status["session_id"])
        self.assertEqual(status["samples_received"], 0)
        self.assertEqual(status["frames_received"], 0)
        self.assertEqual(status["buffer_count"], 0)
        self.assertFalse(status["has_latest_analysis"])
        self.assertIsNone(self.runtime.get_latest_analysis())

    def test_02_explicit_simulator_start(self):
        """2. Explicit simulator start: session created and recording activated."""
        session = self.runtime.start_simulator(seed=42)
        self.assertIsNotNone(session)
        self.assertEqual(session.state, SessionState.RECORDING)
        self.assertEqual(session.source_name, "synthetic")
        self.assertEqual(session.source_type, SignalSourceType.SIMULATOR)

        status = self.runtime.get_runtime_status()
        self.assertEqual(status["state"], "RECORDING")
        self.assertTrue(status["session_active"])

    def test_03_samples_received_tracking(self):
        """3. Samples received tracking: samples and frames increment upon data ingestion."""
        self.runtime.start_simulator(seed=100)
        
        # Manually generate 5 frames of 50 samples = 250 samples
        for _ in range(5):
            frame = self.runtime.synthetic_source.generate_frame(num_samples=50)
            self.runtime.acq_mgr._process_incoming_frame(frame)

        status = self.runtime.get_runtime_status()
        self.assertGreaterEqual(status["samples_received"], 250)
        self.assertGreaterEqual(status["frames_received"], 5)

    def test_04_buffer_population(self):
        """4. Buffer population: rolling buffer holds ingested frames."""
        self.runtime.start_simulator(seed=101)
        for _ in range(3):
            frame = self.runtime.synthetic_source.generate_frame(num_samples=100)
            self.runtime.acq_mgr._process_incoming_frame(frame)

        self.assertGreaterEqual(len(self.runtime.signal_buffer), 300)

    def test_05_analysis_result_generation(self):
        """5. Analysis result generation: quantitative PSD analysis generated when samples >= 32."""
        self.runtime.start_simulator(seed=200)
        for _ in range(5):
            frame = self.runtime.synthetic_source.generate_frame(num_samples=50)
            self.runtime.acq_mgr._process_incoming_frame(frame)

        analysis = self.runtime.run_analysis_tick()
        self.assertIsNotNone(analysis)
        self.assertIn("metrics", analysis)
        self.assertIn("features", analysis)
        self.assertEqual(len(analysis["features"]), 8)

        latest = self.runtime.get_latest_analysis()
        self.assertIsNotNone(latest)
        self.assertIn("metrics", latest)

    def test_06_session_timing(self):
        """6. Session timing: duration increases over time."""
        session = self.runtime.start_simulator(seed=300)
        time.sleep(0.05)
        duration = session.update_duration()
        self.assertGreaterEqual(duration, 0.04)

    def test_07_pause_session(self):
        """7. Pause session: state updates to PAUSED."""
        self.runtime.start_simulator(seed=400)
        self.assertTrue(self.runtime.pause_session())
        status = self.runtime.get_runtime_status()
        self.assertEqual(status["state"], "PAUSED")
        self.assertFalse(status["session_active"])

    def test_08_resume_session(self):
        """8. Resume session: state updates back to RECORDING."""
        self.runtime.start_simulator(seed=500)
        self.runtime.pause_session()
        self.assertTrue(self.runtime.resume_session())
        status = self.runtime.get_runtime_status()
        self.assertEqual(status["state"], "RECORDING")
        self.assertTrue(status["session_active"])

    def test_09_stop_session(self):
        """9. Stop session: halts acquisition, finalizes duration, returns model."""
        self.runtime.start_simulator(seed=600)
        stopped_session = self.runtime.stop_session()
        self.assertIsNotNone(stopped_session)
        self.assertEqual(stopped_session.state, SessionState.STOPPED)
        self.assertIsNotNone(stopped_session.end_timestamp)

        status = self.runtime.get_runtime_status()
        self.assertEqual(status["state"], "STOPPED")
        self.assertFalse(status["session_active"])

    def test_10_zero_input_safety(self):
        """10. Zero-input safety: no fake data or metrics created before explicit start."""
        clean_runtime = RuntimeController(sampling_rate=250)
        self.assertTrue(clean_runtime.is_idle())
        self.assertEqual(len(clean_runtime.signal_buffer), 0)
        self.assertIsNone(clean_runtime.get_latest_analysis())
        self.assertIsNone(clean_runtime.run_analysis_tick())

    def test_11_insufficient_data_behavior(self):
        """11. Insufficient data behavior: < 32 samples returns None without exception."""
        self.runtime.start_simulator(seed=700)
        frame = self.runtime.synthetic_source.generate_frame(num_samples=10) # 10 samples < 32
        self.runtime.acq_mgr._process_incoming_frame(frame)

        result = self.runtime.run_analysis_tick()
        self.assertIsNone(result)

    def test_12_acquisition_error_handling(self):
        """12. Acquisition error handling: invalid source selection raises error cleanly."""
        with self.assertRaises(ValueError):
            self.runtime.start_session(source_name="non_existent_source")
        
        status = self.runtime.get_runtime_status()
        self.assertIn("non_existent_source", status["last_error"])

    def test_13_deterministic_simulator_session(self):
        """13. Deterministic simulator session: fixed seed yields reproducible analysis metrics."""
        r1 = RuntimeController(sampling_rate=250)
        r1.synthetic_source.set_seed(999)
        for _ in range(5):
            f = r1.synthetic_source.generate_frame(num_samples=100)
            r1.acq_mgr._process_incoming_frame(f)
        a1 = r1.run_analysis_tick()

        r2 = RuntimeController(sampling_rate=250)
        r2.synthetic_source.set_seed(999)
        for _ in range(5):
            f = r2.synthetic_source.generate_frame(num_samples=100)
            r2.acq_mgr._process_incoming_frame(f)
        a2 = r2.run_analysis_tick()

        self.assertIsNotNone(a1)
        self.assertIsNotNone(a2)
        self.assertAlmostEqual(a1["metrics"]["dominant_frequency"], a2["metrics"]["dominant_frequency"])
        np.testing.assert_allclose(a1["features"], a2["features"])

    def test_14_pause_timer_freezing_and_resume_duration(self):
        """14. Pause timer freezing: verify timer stops during pause and resumes accurately."""
        session = self.runtime.start_simulator(seed=888)
        time.sleep(0.05)
        self.runtime.pause_session()
        paused_duration = session.update_duration()
        self.assertGreaterEqual(paused_duration, 0.04)

        # Sleep while paused
        time.sleep(0.1)
        during_pause_duration = session.update_duration()
        self.assertEqual(during_pause_duration, paused_duration) # Must remain frozen during pause

        # Resume and sleep
        self.runtime.resume_session()
        time.sleep(0.05)
        resumed_duration = session.update_duration()
        self.assertGreater(resumed_duration, paused_duration)

    def test_15_consecutive_session_counter_resets(self):
        """15. Consecutive session counter resets: verify Session 2 counters start at 0."""
        s1 = self.runtime.start_simulator(seed=123)
        for _ in range(5):
            f = self.runtime.synthetic_source.generate_frame(num_samples=50)
            self.runtime.acq_mgr._process_incoming_frame(f)

        s1_samples = self.runtime.acq_mgr.samples_received
        self.assertGreaterEqual(s1_samples, 250)

        self.runtime.stop_session()

        # Start Session 2
        s2 = self.runtime.start_simulator(seed=456)
        self.assertNotEqual(s1.session_id, s2.session_id)
        
        status = self.runtime.get_runtime_status()
        self.assertLess(status["samples_received"], 20) # Telemetry reset from Session 1 (250+ samples)
        self.assertLessEqual(status["frames_received"], 1)
        self.assertLess(status["buffer_count"], 20)

    def test_16_lifecycle_error_safety_and_edge_cases(self):
        """16. Lifecycle edge cases: pause while idle, resume while recording, double stop."""
        # Pause while idle
        self.assertFalse(self.runtime.pause_session())
        # Resume while idle
        self.assertFalse(self.runtime.resume_session())
        # Stop while idle
        self.assertIsNone(self.runtime.stop_session()) # Returns None if no session exists

        # Start and double stop
        s = self.runtime.start_simulator(seed=789)
        s_stopped1 = self.runtime.stop_session()
        self.assertIsNotNone(s_stopped1)
        end_t1 = s_stopped1.end_timestamp

        time.sleep(0.02)
        s_stopped2 = self.runtime.stop_session()
        self.assertEqual(s_stopped2.end_timestamp, end_t1) # End timestamp preserved

    def test_17_production_logger_integration(self):
        """17. Production logger integration: verify logger is attached and writes log statements."""
        from src.utils.logger import get_logger
        logger = get_logger("test_runtime")
        self.assertIsNotNone(logger)
        self.assertIsNotNone(self.runtime.logger)
        logger.info("Test log statement emitted successfully.")

if __name__ == "__main__":
    unittest.main()
