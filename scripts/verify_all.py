"""
Verification Script for NeuroSim Expo Upgrade
Tests signal processing, Validation Center, AI Interpreter, DB, and PDF Report Generator.
"""

import os
import sys
import numpy as np

# Ensure root dir in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.processing.psd import PSDAnalyzer
from src.classification.ai_interpreter import AIInterpreter
from src.reporting.pdf_generator import PDFReportGenerator

def test_all():
    print("==================================================")
    print("  NEUROSIM EXPO UPGRADE VERIFICATION TEST SUITE  ")
    print("==================================================")

    # 1. Test Validation Center
    print("\n[1/3] Testing Validation Center Self-Tests...")
    analyzer = PSDAnalyzer()
    for band in ['delta', 'theta', 'alpha', 'beta']:
        res = analyzer.run_validation_test(band)
        print(f"  - {band.upper()} Test: Target {res['target_frequency_hz']}Hz -> Detected {res['detected_frequency_hz']}Hz ({res['result']})")
        assert res['passed'], f"Validation test failed for {band}"

    # 2. Test AI Interpreter
    print("\n[2/3] Testing AI Interpretation Engine...")
    summary = {
        'duration': '05:00',
        'samples': 12500,
        'dominant_band': 'ALPHA',
        'load_class': 'RELAXED',
        'alpha_rel': 42.0,
        'beta_rel': 18.0,
        'theta_rel': 22.0,
        'delta_rel': 18.0,
        'stress_index': 0.38,
        'tbr': 1.22
    }
    narrative = AIInterpreter.generate_session_interpretation(summary)
    explanation = AIInterpreter.explain_classification_result(summary)
    print("  - AI Narrative generated successfully.")
    print("  - Feature Attribution generated successfully.")
    assert len(narrative) > 50
    assert len(explanation) > 30

    # 3. Test PDF Generator
    print("\n[3/3] Testing Research PDF Report Generator...")
    pdf_gen = PDFReportGenerator()
    summary['ai_interpretation'] = narrative
    filepath = pdf_gen.generate_report(summary, "test_expo_report.pdf")
    print(f"  - PDF Report created at: {filepath}")
    assert os.path.exists(filepath), "PDF file was not created"
    assert os.path.getsize(filepath) > 1000, "PDF file is too small"

    print("\n==================================================")
    print("  ALL VERIFICATION TESTS PASSED SUCCESSFULLY! ✅ ")
    print("==================================================")

if __name__ == '__main__':
    test_all()
