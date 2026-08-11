"""
Unit Tests — Professional PDF Report Generator
Tests comprehensive PDF report creation with metadata, spectral analysis, 
signal quality metrics, and AI narratives.
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

    def test_pdf_generation_comprehensive(self):
        """Test comprehensive PDF generation with all metadata fields."""
        session_data = {
            'session_id': 'TEST-PDF-002',
            'timestamp': '2026-07-28 12:00:00',
            'duration': 180.0,
            'sample_count': 45000,
            'sampling_rate': 250,
            'source': 'SIMULATION',
            'channel_info': '8-channel EEG (F3, F4, C3, C4, P3, P4, O1, O2)',
            'delta': 15.0,
            'theta': 25.0,
            'alpha': 40.0,
            'beta': 20.0,
            'rel_delta': 15.0,
            'rel_theta': 25.0,
            'rel_alpha': 40.0,
            'rel_beta': 20.0,
            'dominant_band': 'ALPHA',
            'dominant_frequency': 10.5,
            'tbr': 1.25,
            'abr': 2.0,
            'cognitive_state': 'MODERATE',
            'stress_index': 0.45,
            'confidence': 88.0,
            'signal_quality': 92.0,
            'noise_level': 8.0,
            'artifact_rate': 3.5,
            'snr': 24.5
        }
        
        res_path = PDFReportGenerator.generate_report(session_data, self.tmp_pdf.name)
        
        self.assertTrue(os.path.exists(res_path))
        self.assertGreater(os.path.getsize(res_path), 4000)  # Comprehensive report should be substantial
        
    def test_pdf_generation_minimal(self):
        """Test PDF generation with minimal data (backward compatibility)."""
        session_data = {
            'session_id': 'TEST-MINIMAL-001',
            'cognitive_state': 'RELAXED',
            'stress_index': 0.3
        }
        
        tmp_minimal = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        tmp_minimal.close()
        
        try:
            res_path = PDFReportGenerator.generate_report(session_data, tmp_minimal.name)
            self.assertTrue(os.path.exists(res_path))
            self.assertGreater(os.path.getsize(res_path), 1000)
        finally:
            if os.path.exists(tmp_minimal.name):
                os.remove(tmp_minimal.name)

    def test_narrative_generation(self):
        """Test AI narrative generation logic."""
        # Low stress scenario
        low_stress = {'stress_index': 0.2, 'dominant_band': 'ALPHA', 'cognitive_state': 'RELAXED', 'signal_quality': 95.0}
        narrative_low = PDFReportGenerator._generate_narrative(low_stress)
        self.assertIn("minimal levels", narrative_low)
        self.assertIn("excellent", narrative_low)
        
        # High stress scenario
        high_stress = {'stress_index': 0.7, 'dominant_band': 'BETA', 'cognitive_state': 'HIGH_LOAD', 'signal_quality': 55.0}
        narrative_high = PDFReportGenerator._generate_narrative(high_stress)
        self.assertIn("Elevated stress", narrative_high)
        self.assertIn("caution", narrative_high)

    def test_band_power_calculation(self):
        """Test band power table generation with automatic relative calculation."""
        session_data = {
            'delta': 10.0,
            'theta': 20.0,
            'alpha': 50.0,
            'beta': 20.0
        }
        
        from reportlab.lib.styles import getSampleStyleSheet
        style = getSampleStyleSheet()['BodyText']
        
        table = PDFReportGenerator._build_band_power_table(session_data, style)
        self.assertIsNotNone(table)


if __name__ == '__main__':
    unittest.main()
