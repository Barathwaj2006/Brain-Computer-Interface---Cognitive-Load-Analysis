"""Focused integration tests for Browser -> API -> RuntimeController."""

import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PySide6.QtWidgets import QApplication

from runtime_service import RuntimeService
from serve_local import create_server


app = QApplication.instance() or QApplication([])


class TestRuntimeApiBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = RuntimeService()
        cls.server = create_server(port=0, runtime_service=cls.service)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.service.runtime.stop_session()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request_json(self, path, method="GET"):
        request = Request(f"{self.base_url}{path}", method=method)
        with urlopen(request, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))

    def populate_runtime(self, frames=8, samples_per_frame=50):
        for _ in range(frames):
            frame = self.service.runtime.synthetic_source.generate_frame(samples_per_frame)
            self.service.runtime.acq_mgr._process_incoming_frame(frame)

    def test_01_zero_input_state_is_truthful(self):
        state = self.request_json("/api/state")
        self.assertFalse(state["streaming"])
        self.assertEqual(state["samples"], 0)
        self.assertFalse(state["analysis_available"])
        self.assertIsNone(state["metrics"])
        waveform = self.request_json("/api/waveform?seconds=5")
        self.assertEqual(waveform["channels"]["FP1"], [])

    def test_02_lifecycle_waveform_analysis_and_second_session(self):
        started = self.request_json("/api/session/start", "POST")
        self.assertTrue(started["streaming"])
        self.assertEqual(started["samples"], 0)

        self.populate_runtime()
        state = self.request_json("/api/state")
        self.assertGreaterEqual(state["samples"], 400)
        self.assertTrue(state["analysis_available"])
        self.assertIn("total_power", state["metrics"])

        waveform = self.request_json("/api/waveform?seconds=1")
        self.assertEqual(set(waveform["channels"]), {"FP1", "FP2", "O1", "O2"})
        self.assertGreater(len(waveform["channels"]["FP1"]), 0)
        analysis = self.request_json("/api/analysis")["analysis"]
        self.assertIsNotNone(analysis)
        self.assertIn("spectrum", analysis)

        paused = self.request_json("/api/session/pause", "POST")
        self.assertTrue(paused["paused"])
        paused_samples = paused["samples"]
        self.assertEqual(self.request_json("/api/state")["samples"], paused_samples)

        resumed = self.request_json("/api/session/resume", "POST")
        self.assertTrue(resumed["streaming"])
        self.populate_runtime(frames=2)
        self.assertGreater(self.request_json("/api/state")["samples"], paused_samples)

        stopped = self.request_json("/api/session/stop", "POST")
        self.assertFalse(stopped["streaming"])
        self.assertEqual(stopped["state"], "STOPPED")

        report = Request(f"{self.base_url}/api/report", method="POST")
        with urlopen(report, timeout=3) as response:
            self.assertEqual(response.headers.get_content_type(), "application/pdf")
            self.assertTrue(response.read().startswith(b"%PDF"))

        second = self.request_json("/api/session/start", "POST")
        self.assertTrue(second["streaming"])
        self.assertEqual(second["samples"], 0)
        self.assertEqual(second["buffer_count"], 0)
        self.request_json("/api/session/stop", "POST")

    def test_03_malformed_and_unavailable_requests_fail_safely(self):
        with self.assertRaises(HTTPError) as invalid_window:
            self.request_json("/api/waveform?seconds=invalid")
        self.assertEqual(invalid_window.exception.code, 400)

        with self.assertRaises(HTTPError) as missing_endpoint:
            self.request_json("/api/does-not-exist")
        self.assertEqual(missing_endpoint.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
