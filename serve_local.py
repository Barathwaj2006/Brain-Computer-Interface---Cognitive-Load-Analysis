#!/usr/bin/env python3
"""Serve the browser UI and its thin API bridge to RuntimeController."""

from __future__ import annotations

import argparse
import json
import os
import signal
import tempfile
import threading
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PySide6.QtCore import QCoreApplication

from runtime_service import RuntimeService
from src.reporting.pdf_generator import PDFReportGenerator

WEB_DIR = Path(__file__).resolve().parent / "web"


class NeuroSimRequestHandler(SimpleHTTPRequestHandler):
    """Static-file handler with a deliberately small JSON API surface."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    @property
    def runtime_service(self) -> RuntimeService:
        return self.server.runtime_service

    def log_message(self, format, *args):
        return

    def _json(self, payload, status=HTTPStatus.OK):
        encoded = json.dumps(payload, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _error(self, status, message):
        self._json({"error": message}, status)

    def do_GET(self):
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            return super().do_GET()
        try:
            if parsed.path == "/api/history":
                return self._json({"sessions": self.runtime_service.history()})
            if parsed.path == "/api/settings":
                return self._json(self.runtime_service.settings())
            if parsed.path == "/api/state":
                return self._json(self.runtime_service.state())
            if parsed.path == "/api/analysis":
                return self._json({"analysis": self.runtime_service.analysis()})
            if parsed.path == "/api/waveform":
                seconds = float(parse_qs(parsed.query).get("seconds", ["5"])[0])
                return self._json(self.runtime_service.waveform(seconds))
            return self._error(HTTPStatus.NOT_FOUND, "Unknown API endpoint")
        except (ValueError, RuntimeError) as error:
            return self._error(HTTPStatus.BAD_REQUEST, str(error))
        except Exception as error:
            return self._error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            actions = {
                "/api/session/start": self.runtime_service.start,
                "/api/session/pause": self.runtime_service.pause,
                "/api/session/resume": self.runtime_service.resume,
                "/api/session/stop": self.runtime_service.stop,
            }
            if parsed.path in actions:
                return self._json(actions[parsed.path]())
            if parsed.path == "/api/history/delete":
                params = parse_qs(parsed.query)
                session_id = params.get("session_id", [None])[0]
                if not session_id:
                    return self._error(HTTPStatus.BAD_REQUEST, "Missing required query parameter: session_id")
                return self._json(self.runtime_service.delete_history(session_id))
            if parsed.path == "/api/report":
                params = parse_qs(parsed.query)
                session_id = params.get("session_id", [None])[0]
                report_data = self.runtime_service.report_data(session_id=session_id)
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as file:
                    report_path = file.name
                try:
                    PDFReportGenerator.generate_report(report_data, report_path)
                    content = Path(report_path).read_bytes()
                finally:
                    if os.path.exists(report_path):
                        os.remove(report_path)
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", f'attachment; filename="NeuroSim_{report_data["session_id"]}.pdf"')
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            return self._error(HTTPStatus.NOT_FOUND, "Unknown API endpoint")
        except RuntimeError as error:
            return self._error(HTTPStatus.CONFLICT, str(error))
        except Exception as error:
            return self._error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))


def create_server(host="127.0.0.1", port=8000, runtime_service=None):
    server = ThreadingHTTPServer((host, port), NeuroSimRequestHandler)
    server.runtime_service = runtime_service or RuntimeService()
    return server


def run(host="127.0.0.1", port=8000, open_browser=True):
    app = QCoreApplication.instance() or QCoreApplication([])
    server = create_server(host, port)
    thread = threading.Thread(target=server.serve_forever, name="neurosim-api", daemon=True)
    thread.start()
    url = f"http://{host}:{server.server_port}"
    print(f"NeuroSim browser application listening on {url}")
    if open_browser:
        webbrowser.open(url)

    def shutdown():
        server.shutdown()
        server.server_close()

    app.aboutToQuit.connect(shutdown)
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    return app.exec()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    options = parser.parse_args()
    run(options.host, options.port, not options.no_browser)
