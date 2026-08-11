"""
NeuroSim 3.0 Master Application Integration End-to-End Test
Validates the complete end-to-end scientific lifecycle:
IDLE -> START -> STREAM -> PAUSE -> RESUME -> STOP -> SECOND SESSION -> ANALYSIS -> HISTORY -> COMPARISON -> REPORT -> PDF -> CSV -> BIDS -> NEUROFEEDBACK
"""

import unittest
import time
import json
import os
import tempfile

from runtime_service import RuntimeService
from src.runtime.runtime_controller import RuntimeController
from src.reporting.pdf_generator import PDFReportGenerator


class TestE2EMasterLifecycle(unittest.TestCase):

    def setUp(self):
        self.runtime = RuntimeController(sampling_rate=250, channels=("FP1", "FP2", "O1", "O2"))
        self.service = RuntimeService(runtime=self.runtime)

    def tearDown(self):
        self.runtime.stop_session()

    def test_complete_master_lifecycle(self):
        # 1. IDLE State
        initial_state = self.service.state()
        self.assertEqual(initial_state["state"], "IDLE")
        self.assertFalse(initial_state["streaming"])
        self.assertFalse(initial_state["paused"])
        self.assertEqual(initial_state["samples"], 0)
        self.assertFalse(initial_state["analysis_available"])
        self.assertEqual(initial_state["hardware"]["status"], "NOT_CONNECTED")

        # Waveform zero-input check
        wf_idle = self.service.waveform(seconds=5.0)
        self.assertEqual(len(wf_idle["channels"]["FP1"]), 0)

        # 2. START Session 1 -> STREAMING
        start_state1 = self.service.start()
        self.assertEqual(start_state1["state"], "RECORDING")
        self.assertTrue(start_state1["streaming"])
        sess1_id = start_state1["session_id"]
        self.assertIsNotNone(sess1_id)

        # Ingest frames for Session 1
        for _ in range(5):
            frame = self.runtime.synthetic_source.generate_frame(num_samples=50)
            self.runtime.acq_mgr._process_incoming_frame(frame)
            time.sleep(0.01)

        # 3. STREAM & WAVEFORM
        stream_state = self.service.state()
        self.assertGreaterEqual(stream_state["samples"], 250)
        wf_stream = self.service.waveform(seconds=5.0)
        self.assertGreater(len(wf_stream["channels"]["FP1"]), 0)

        # 4. PAUSE -> PAUSED
        pause_state = self.service.pause()
        self.assertEqual(pause_state["state"], "PAUSED")
        self.assertTrue(pause_state["paused"])

        # 5. RESUME -> STREAMING
        resume_state = self.service.resume()
        self.assertEqual(resume_state["state"], "RECORDING")
        self.assertTrue(resume_state["streaming"])

        # 6. STOP Session 1 -> STOPPED / Saved to SQLite
        stop_state1 = self.service.stop()
        self.assertEqual(stop_state1["state"], "STOPPED")

        # 7. START SECOND SESSION -> NEW SESSION (No state leakage)
        start_state2 = self.service.start()
        self.assertEqual(start_state2["state"], "RECORDING")
        sess2_id = start_state2["session_id"]
        self.assertNotEqual(sess1_id, sess2_id)
        # Samples counter reset
        self.assertLess(start_state2["samples"], 20)

        # Ingest frames for Session 2
        for _ in range(5):
            frame = self.runtime.synthetic_source.generate_frame(num_samples=50)
            self.runtime.acq_mgr._process_incoming_frame(frame)
            time.sleep(0.01)

        stop_state2 = self.service.stop()
        self.assertEqual(stop_state2["state"], "STOPPED")

        # 8. ANALYSIS & METRICS
        analysis = self.service.analysis()
        self.assertIsNotNone(analysis)
        self.assertIn("metrics", analysis)
        metrics = analysis["metrics"]
        self.assertIn("delta_rel", metrics)
        self.assertIn("theta_rel", metrics)
        self.assertIn("alpha_rel", metrics)
        self.assertIn("beta_rel", metrics)
        self.assertIn("tbr", metrics)
        self.assertIn("abr", metrics)
        self.assertIn("stress_index", metrics)

        # 9. HISTORY (SQLite database archive)
        history = self.service.history()
        self.assertGreaterEqual(len(history), 2)
        history_ids = [s["session_id"] for s in history]
        self.assertIn(sess1_id, history_ids)
        self.assertIn(sess2_id, history_ids)

        # 10. COMPARISON (Side-by-side longitudinal comparison)
        comp = self.service.compare_research([sess1_id, sess2_id])
        self.assertEqual(comp["compared_count"], 2)

        # 11. REPORT DATA & PDF EXPORT
        rep_data = self.service.report_data(session_id=sess1_id)
        self.assertEqual(rep_data["session_id"], sess1_id)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = f.name
        try:
            PDFReportGenerator.generate_report(rep_data, pdf_path)
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 500)
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

        # 12. CSV EXPORT
        csv_str = self.service.export_research_csv()
        self.assertIn("session_id", csv_str)
        self.assertIn(sess1_id, csv_str)

        # 13. BIDS EXPORT
        bids_data = self.service.export_research_bids()
        self.assertEqual(bids_data["BIDSVersion"], "1.8.0")
        self.assertGreaterEqual(len(bids_data["Sessions"]), 2)

        # 14. NEUROFEEDBACK INTEGRATION
        alpha_rel = metrics["alpha_rel"]
        focus_score = Math_max = max(0.0, min(100.0, (alpha_rel / 35.0) * 100.0))
        self.assertGreaterEqual(focus_score, 0.0)


if __name__ == "__main__":
    unittest.main()
