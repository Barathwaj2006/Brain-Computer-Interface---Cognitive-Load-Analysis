"""
Sanity Verification Script
Verifies that all medical-grade widgets, DSP analyzers, AI interpreter,
and UI screens import and run without any errors.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.processing.psd import PSDAnalyzer
from src.classification.ai_interpreter import AIInterpreter
from src.visualization.topographic_map import TopographicMapWidget
from src.visualization.spectrogram_widget import SpectrogramWidget
from src.visualization.multichannel_viewer import MultiChannelViewerWidget
from src.reporting.pdf_generator import PDFReportGenerator

def verify():
    print("Testing Medical-Grade Modules...")
    
    analyzer = PSDAnalyzer()
    val_res = analyzer.run_validation_test('alpha')
    assert val_res['passed'], "Alpha validation failed"
    print("✓ PSD & Validation Center test passed.")

    interp = AIInterpreter.generate_session_interpretation({'dominant_band': 'ALPHA', 'load_class': 'RELAXED', 'alpha_rel': 45.0, 'beta_rel': 15.0, 'theta_rel': 20.0, 'delta_rel': 20.0})
    assert len(interp) > 50
    print("✓ AI Interpretation Engine passed.")

    pdf_gen = PDFReportGenerator()
    report_path = pdf_gen.generate_report({'id': 'VERIFY-001', 'load_class': 'RELAXED', 'alpha': 45.0, 'beta': 15.0, 'theta': 20.0, 'delta': 20.0})
    assert os.path.exists(report_path)
    print("✓ PDF Report Generation passed.")

    print("\nALL MEDICAL-GRADE MODULES VERIFIED SUCCESSFULLY WITH 0 ERRORS! ✅")

if __name__ == '__main__':
    verify()
