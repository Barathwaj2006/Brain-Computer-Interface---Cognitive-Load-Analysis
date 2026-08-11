"""
Unit & Integration Test Suite for NeuroSim API Server (serve_local.py & runtime_service.py)
Validates all HTTP API endpoints, JSON responses, error handling, session archive queries, and PDF generation.
"""

import unittest
import time
import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import threading

from serve_local import create_server
from runtime_service import RuntimeService
from src.runtime.runtime_controller import RuntimeController


class TestAPIServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.runtime = RuntimeController(sampling_rate=250, channels=("FP1", "FP2"))
        cls.service = RuntimeService(runtime=cls.runtime)
        cls.server = create_server(host="127.0.0.1", port=0, runtime_service=cls.service)
        cls.port = cls.server.server_port
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.runtime.stop_session()
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.runtime.stop_session()

    def _get(self, path: str):
        url = f"{self.base_url}{path}"
        req = Request(url)
        with urlopen(req) as resp:
            data = resp.read()
            content_type = resp.headers.get("Content-Type", "")
            return resp.status, content_type, data

    def _post(self, path: str):
        url = f"{self.base_url}{path}"
        req = Request(url, method="POST")
        with urlopen(req) as resp:
            data = resp.read()
            content_type = resp.headers.get("Content-Type", "")
            return resp.status, content_type, data

    def test_01_get_state_idle(self):
        """Verify GET /api/state returns idle state with zero samples."""
        status, content_type, data = self._get("/api/state")
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        payload = json.loads(data.decode("utf-8"))
        self.assertEqual(payload["state"], "IDLE")
        self.assertFalse(payload["streaming"])
        self.assertEqual(payload["samples"], 0)

    def test_02_get_waveform(self):
        """Verify GET /api/waveform returns 5-second default channels."""
        status, content_type, data = self._get("/api/waveform?seconds=5")
        self.assertEqual(status, 200)
        payload = json.loads(data.decode("utf-8"))
        self.assertEqual(payload["seconds"], 5.0)
        self.assertIn("FP1", payload["channels"])

    def test_03_get_history(self):
        """Verify GET /api/history returns sessions list."""
        status, content_type, data = self._get("/api/history")
        self.assertEqual(status, 200)
        payload = json.loads(data.decode("utf-8"))
        self.assertIn("sessions", payload)
        self.assertIsInstance(payload["sessions"], list)

    def test_03b_get_settings(self):
        """Verify GET /api/settings returns system configuration."""
        status, content_type, data = self._get("/api/settings")
        self.assertEqual(status, 200)
        payload = json.loads(data.decode("utf-8"))
        self.assertIn("app_name", payload)
        self.assertEqual(payload["sampling_rate"], 250)

    def test_04_session_lifecycle(self):
        """Verify POST /api/session/start, pause, resume, and stop."""
        # START
        status, _, data = self._post("/api/session/start")
        self.assertEqual(status, 200)
        payload = json.loads(data.decode("utf-8"))
        self.assertEqual(payload["state"], "RECORDING")
        self.assertTrue(payload["streaming"])

        # Wait for data ingestion
        time.sleep(0.3)

        # PAUSE
        status, _, data = self._post("/api/session/pause")
        self.assertEqual(status, 200)
        payload = json.loads(data.decode("utf-8"))
        self.assertEqual(payload["state"], "PAUSED")
        self.assertTrue(payload["paused"])

        # RESUME
        status, _, data = self._post("/api/session/resume")
        self.assertEqual(status, 200)
        payload = json.loads(data.decode("utf-8"))
        self.assertEqual(payload["state"], "RECORDING")

        time.sleep(0.2)

        # STOP
        status, _, data = self._post("/api/session/stop")
        self.assertEqual(status, 200)
        payload = json.loads(data.decode("utf-8"))
        self.assertEqual(payload["state"], "STOPPED")

    def test_05_pdf_report_export(self):
        """Verify POST /api/report exports valid PDF for completed session."""
        # Start and run session to generate analysis
        self._post("/api/session/start")
        time.sleep(0.5)
        self._post("/api/session/stop")

        status, content_type, data = self._post("/api/report")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/pdf")
        self.assertTrue(data.startswith(b"%PDF"))

    def test_06_error_handling_invalid_endpoint(self):
        """Verify 404 response for non-existent API endpoint."""
        with self.assertRaises(HTTPError) as ctx:
            self._get("/api/unknown_endpoint")
        self.assertEqual(ctx.exception.code, 404)

    def test_07_delete_history(self):
        """Verify POST /api/history/delete removes session from database."""
        # Create a saved session
        self._post("/api/session/start")
        time.sleep(0.5)
        self._post("/api/session/stop")
        
        _, _, data = self._get("/api/history")
        sessions = json.loads(data.decode("utf-8"))["sessions"]
        if sessions:
            target_id = sessions[0]["session_id"]
            status, _, del_data = self._post(f"/api/history/delete?session_id={target_id}")
            self.assertEqual(status, 200)
            res = json.loads(del_data.decode("utf-8"))
            self.assertEqual(res["deleted"], target_id)


if __name__ == "__main__":
    unittest.main()
