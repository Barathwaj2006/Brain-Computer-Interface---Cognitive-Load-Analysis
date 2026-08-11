"""
NeuroSim 3.0 Research Platform Test Suite
Validates longitudinal analytics, multi-session comparison matrices, BIDS exporting,
and research CSV dataset generation.
"""

import unittest
import json
import time
import os
import tempfile
from urllib.request import urlopen, Request
from urllib.error import HTTPError

from serve_local import create_server
from src.analysis.research_engine import ResearchAnalyticsEngine
from src.database.db_manager import DatabaseManager


class TestResearchPlatform(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_file = os.path.join(tempfile.gettempdir(), f"neurosim_test_research_{int(time.time())}.db")
        cls.db_mgr = DatabaseManager(db_path=cls.db_file)
        cls.engine = ResearchAnalyticsEngine(db_manager=cls.db_mgr)

        # Seed test sessions
        cls.db_mgr.save_session({
            "session_id": "SES-TEST-001",
            "duration": 60.0,
            "sampling_rate": 250,
            "mode": "SIMULATOR",
            "rel_delta": 20.0,
            "rel_theta": 20.0,
            "rel_alpha": 40.0,
            "rel_beta": 20.0,
            "dominant_band": "ALPHA",
            "cognitive_state": "MODERATE",
            "stress_index": 0.45,
            "confidence": 88.0,
            "notes": "Research Test Session 1"
        })
        cls.db_mgr.save_session({
            "session_id": "SES-TEST-002",
            "duration": 120.0,
            "sampling_rate": 250,
            "mode": "SIMULATOR",
            "rel_delta": 15.0,
            "rel_theta": 15.0,
            "rel_alpha": 30.0,
            "rel_beta": 40.0,
            "dominant_band": "BETA",
            "cognitive_state": "HIGH",
            "stress_index": 0.75,
            "confidence": 92.0,
            "notes": "Research Test Session 2"
        })

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_file):
            try:
                os.remove(cls.db_file)
            except Exception:
                pass

    def test_01_longitudinal_analytics_summary(self):
        """1. Verify longitudinal analytics computation across sessions."""
        summary = self.engine.get_longitudinal_summary()
        self.assertEqual(summary["total_sessions"], 2)
        self.assertEqual(summary["total_duration_sec"], 180.0)
        self.assertEqual(summary["avg_duration_sec"], 90.0)
        self.assertEqual(summary["mean_stress_index"], 0.6)
        self.assertEqual(len(summary["timeline"]), 2)

    def test_02_session_comparison(self):
        """2. Verify side-by-side session comparison matrix."""
        comp = self.engine.compare_sessions(["SES-TEST-001", "SES-TEST-002"])
        self.assertEqual(comp["compared_count"], 2)
        self.assertEqual(comp["sessions"][0]["session_id"], "SES-TEST-001")
        self.assertEqual(comp["sessions"][1]["session_id"], "SES-TEST-002")

    def test_03_csv_dataset_export(self):
        """3. Verify CSV dataset output generation."""
        csv_text = self.engine.export_csv_summary()
        self.assertIn("session_id,timestamp,duration_sec", csv_text)
        self.assertIn("SES-TEST-001", csv_text)
        self.assertIn("SES-TEST-002", csv_text)

    def test_04_bids_dataset_export(self):
        """4. Verify BIDS JSON dataset output structure."""
        bids = self.engine.export_bids_dataset()
        self.assertEqual(bids["BIDSVersion"], "1.8.0")
        self.assertEqual(len(bids["Sessions"]), 2)
        self.assertEqual(bids["Sessions"][0]["ses"], "SES-TEST-001")


if __name__ == "__main__":
    unittest.main()
