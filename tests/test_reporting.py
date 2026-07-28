"""
Unit Tests — Biomedical PDF Report Generator
Tests PDF report creation and verifies output file exists.
"""

import os
import unittest
import tempfile
from src.reporting.pdf_generator import PDFReportGenerator

class TestReporting(unittest.TestCase):
    def setUp(self):
        self.tmp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        self.tmp_pdf.close()

    def tearDown(self):
        if os.path.exists(self.tmp_pdf.name):
            try:
                os.remove(self.tmp_pdf.name)
            except OSError:
                pass

    def test_pdf_generation(self):
        session_data = {
            'session_id': 'TEST-PDF-001',
            'timestamp': '2026-07-28 12:00:00',
            'duration': 180.0,
            'sampling_rate': 250,
            'mode': 'SIMULATION',
            'rel_delta': 15.0,
            'rel_theta': 25.0,
            'rel_alpha': 40.0,
            'rel_beta': 20.0,
            'dominant_band': 'ALPHA',
            'cognitive_state': 'MODERATE',
            'stress_index': 0.5,
            'confidence': 88.0
        }
        res_path = PDFReportGenerator.generate_report(session_data, self.tmp_pdf.name)
        self.assertTrue(os.path.exists(res_path))
        self.assertGreater(os.path.getsize(res_path), 1000)

if __name__ == '__main__':
    unittest.main()
