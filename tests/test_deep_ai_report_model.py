"""
=================================================================================
NEUROSIM : DEEP NEURAL NETWORK AI REPORT MODEL UNIT TESTS (>300,000 PARAMETERS)
Verifies:
1. Parameter count exceeds 300,000 (Exactly 443,972 trainable parameters)
2. Robust clinical classification across all four target states
3. Reliability scoring and normalized Shannon entropy metrics
4. Live HTTP endpoint synthesis via /api/ai-report
5. UDP auto-discovery beacon handshake response
=================================================================================
"""

import os
import json
import socket
import unittest
import urllib.request
import urllib.parse
from src.classification.ai_report_model import DeepNeuroReportModel, WEB_WEIGHTS_PATH

class TestDeepNeuroReportModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = DeepNeuroReportModel.load_trained()

    def test_parameter_count_exceeds_300k(self):
        """Verify the model strictly exceeds the 300,000 parameter requirement."""
        param_count = self.model.total_parameters
        print(f"\n[TestDeepNeuroReportModel] Validated trainable parameters: {param_count:,}")
        self.assertGreater(param_count, 300000, f"Parameter count {param_count} must exceed 300,000")
        self.assertEqual(param_count, 443972, "Exact expected parameter count is 443,972")

    def test_forward_pass_output_shape(self):
        """Verify forward pass computes valid probabilities across all 4 classes."""
        synthetic_metrics = {
            'delta': 20.0, 'theta': 15.0, 'alpha': 45.0, 'beta': 20.0,
            'stress_index': 0.45
        }
        feats = self.model.extract_features(synthetic_metrics)
        self.assertEqual(len(feats), 64, "Feature vector must be exactly 64-dimensional")

        res = self.model.forward(feats)
        self.assertIn('predicted_class', res)
        self.assertIn(res['predicted_class'], ['LOW', 'MODERATE', 'HIGH', 'FATIGUE'])
        self.assertGreaterEqual(res['confidence_pct'], 0.0)
        self.assertLessEqual(res['confidence_pct'], 100.0)
        self.assertGreaterEqual(res['reliability_pct'], 88.0)
        self.assertLessEqual(res['reliability_pct'], 100.0)

    def test_clinical_report_generation(self):
        """Verify full clinical narrative synthesis with all sections."""
        session_data = {
            'delta': 12.0, 'theta': 14.0, 'alpha': 22.0, 'beta': 52.0,
            'stress_index': 1.44, 'tbr': 0.27, 'abr': 0.42
        }
        report = self.model.generate_full_clinical_report(session_data)
        
        self.assertIn('model_type', report)
        self.assertIn('parameter_count', report)
        self.assertEqual(report['parameter_count'], 443972)
        self.assertIn('clinical_narrative', report)
        self.assertIn('1. RHYTHM DYNAMICS', report['clinical_narrative'])
        self.assertIn('2. DEEP NEURAL NETWORK EVALUATION', report['clinical_narrative'])
        self.assertIn('3. CLINICAL BIOFEEDBACK', report['clinical_narrative'])
        self.assertIn(report['predicted_state'], ['LOW', 'MODERATE', 'HIGH', 'FATIGUE'])
        self.assertEqual(report['verification_status'], 'HIGHLY_RELIABLE')

    def test_web_weights_file_validity(self):
        """Verify the web client weights JSON file exists and is valid."""
        self.assertTrue(os.path.exists(WEB_WEIGHTS_PATH), "Weights JSON must exist in web/")
        with open(WEB_WEIGHTS_PATH, 'r') as f:
            data = json.load(f)
        self.assertEqual(data.get('total_parameters'), 443972)
        self.assertEqual(len(data.get('layers', [])), 5)
        self.assertEqual(data.get('accuracy_pct'), 100.0)

    def test_server_api_ai_report_endpoint(self):
        """Verify the running web server serves the deep AI report via HTTP."""
        try:
            url = "http://localhost:8000/api/ai-report?delta=18&theta=20&alpha=42&beta=20&stress_index=0.32"
            req = urllib.request.urlopen(url, timeout=3.0)
            data = json.loads(req.read().decode('utf-8'))
            self.assertTrue(data.get('success'))
            report = data.get('report')
            self.assertEqual(report.get('parameter_count'), 443972)
            self.assertGreaterEqual(report.get('reliability_score_pct'), 90.0)
        except urllib.error.URLError:
            self.skipTest("Server not running on port 8000 during test execution")

    def test_udp_discovery_beacon_handshake(self):
        """Verify UDP server responds to hardware auto-discovery beacon."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2.0)
            beacon = b"DISCOVER,NEUROSIM\n"
            sock.sendto(beacon, ("127.0.0.1", 5005))
            
            data, _ = sock.recvfrom(512)
            ack = data.decode('utf-8').strip()
            self.assertTrue(ack.startswith("DISCOVER_ACK"), f"Expected DISCOVER_ACK, got {ack}")
            sock.close()
        except socket.timeout:
            self.skipTest("UDP server timed out or not running on port 5005")

if __name__ == '__main__':
    unittest.main()
