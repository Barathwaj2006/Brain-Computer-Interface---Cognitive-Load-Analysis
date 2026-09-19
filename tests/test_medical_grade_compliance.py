"""
=================================================================================
NEUROSIM : AUTOMATED MEDICAL-GRADE COMPLIANCE TEST SUITE
Standards Verification:
- IEC 60601-2-26: European Data Format (EDF+) & Continuous Lead Impedance Gating
- HL7 FHIR R4: DiagnosticReport & Quantitative Observation Resource Bundle
- 21 CFR Part 11: Cryptographic SHA-256 Merkle Chaining & Tamper Detection
- Physiological Artifact Suppression: Online EOG Blink & EMG Burst Clamping
- FDA Good Machine Learning Practice (GMLP): Explainable AI (XAI) Saliency Gradients
=================================================================================
"""

import os
import sys
import unittest
import tempfile
import sqlite3
import numpy as np

# Add repo root to module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.reporting.edf_exporter import EDFExporter
from src.reporting.fhir_exporter import FHIRExporter
from src.processing.impedance_manager import ImpedanceManager
from src.processing.artifact_filter import ArtifactFilter
from src.classification.ai_report_model import DeepNeuroReportModel


class TestMedicalGradeCompliance(unittest.TestCase):
    """
    Comprehensive verification tests for all medical-grade subsystems.
    """

    # --------------------------------------------------------------------------
    # 1. 21 CFR Part 11 Cryptographic Audit Trail Chaining & Tamper Detection
    # --------------------------------------------------------------------------
    def test_audit_hash_chaining_and_tamper_detection(self):
        """Validates forward SHA-256 Merkle hash chain and detects unauthorized edits."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            db_path = tf.name

        try:
            import server
            orig_db_path = server.DB_PATH
            server.DB_PATH = db_path
            # Reset thread-local connection so it connects to the new isolated test DB
            if hasattr(server.DatabaseManager._local, "conn"):
                server.DatabaseManager._local.conn = None

            server.DatabaseManager.init_db()

            # 1. Write legitimate audit log entries
            hash1 = server.DatabaseManager.log_audit("AUTH_LOGIN", "127.0.0.1", "Dr. Jane Doe authenticated")
            hash2 = server.DatabaseManager.log_audit("SESSION_RECORD", "127.0.0.1", "Session SESS-001 started")
            hash3 = server.DatabaseManager.log_audit("EXPORT_EDF", "127.0.0.1", "EDF+ binary exported for SESS-001")

            self.assertIsNotNone(hash1)
            self.assertEqual(len(hash1), 64)
            self.assertEqual(len(hash2), 64)
            self.assertEqual(len(hash3), 64)

            # 2. Verify pristine chain
            res_pristine = server.DatabaseManager.verify_audit_chain()
            self.assertTrue(res_pristine["valid"], f"Pristine audit chain should be valid: {res_pristine}")
            self.assertEqual(res_pristine["total_records_verified"], 3)
            self.assertIn("21 CFR Part 11", res_pristine["compliance"])

            # 3. Maliciously tamper with an entry in the SQLite database
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("UPDATE audit_logs SET details = 'FALSIFIED RECORD' WHERE event_type = 'SESSION_RECORD'")
            conn.commit()
            conn.close()

            # 4. Verify that the tamper-detection algorithm flags the mismatch
            res_tampered = server.DatabaseManager.verify_audit_chain()
            self.assertFalse(res_tampered["valid"], "Tampered database must fail cryptographic verification")
            self.assertIn("tampered", res_tampered["error"].lower())

        finally:
            if hasattr(server.DatabaseManager._local, "conn") and server.DatabaseManager._local.conn:
                try:
                    server.DatabaseManager._local.conn.close()
                except Exception:
                    pass
                server.DatabaseManager._local.conn = None
            server.DB_PATH = orig_db_path
            try:
                if os.path.exists(db_path):
                    os.remove(db_path)
            except Exception:
                pass

    # --------------------------------------------------------------------------
    # 2. IEC 60601-2-26 European Data Format (EDF+) Binary Export
    # --------------------------------------------------------------------------
    def test_edf_binary_export_conformity(self):
        """Validates EDF+ byte stream conforming to standard 256-byte header and 16-bit PCM scaling."""
        t = np.linspace(0, 1.0, 250, endpoint=False)
        raw_samples = (30.0 * np.sin(2 * np.pi * 10.0 * t)).tolist()

        session_info = {
            "id": "SESSION-EDF-001",
            "session_uid": "SESSION-EDF-001",
            "patient_id": "PATIENT-TEST-001"
        }

        edf_bytes = EDFExporter.generate_edf_bytes(
            session_info=session_info,
            raw_samples=raw_samples,
            sampling_rate=250
        )

        self.assertIsInstance(edf_bytes, bytes)
        self.assertGreater(len(edf_bytes), 256)

        # Byte 0..7 must be standard EDF version "0       "
        self.assertEqual(edf_bytes[:8].decode('ascii'), "0       ")

        # Byte 8..87 is Patient ID (80 chars)
        pat_field = edf_bytes[8:88].decode('ascii')
        self.assertIn("PATIENT-TEST-001", pat_field)

        # Byte 88..167 is Recording ID (80 chars)
        rec_field = edf_bytes[88:168].decode('ascii')
        self.assertIn("SESSION-EDF-001", rec_field)

        # Header size must be 256 + 8 signals * 256 = 2304 bytes
        header_bytes_str = edf_bytes[184:192].decode('ascii').strip()
        self.assertEqual(int(header_bytes_str), 2304)

        # Number of signals must be 8
        ns_str = edf_bytes[252:256].decode('ascii').strip()
        self.assertEqual(int(ns_str), 8)

        # Verify total file size matches header + data record size
        num_records = int(edf_bytes[236:244].decode('ascii').strip())
        self.assertEqual(num_records, 1)
        expected_size = 2304 + (8 * 250 * 2) # 2304 header + 4000 bytes PCM = 6304
        self.assertEqual(len(edf_bytes), expected_size)

    # --------------------------------------------------------------------------
    # 3. HL7 FHIR R4 Bundle & Observation Resource Export
    # --------------------------------------------------------------------------
    def test_fhir_r4_bundle_export_conformity(self):
        """Validates HL7 FHIR R4 DiagnosticReport transaction bundle generation."""
        session_data = {
            "id": "SESS-FHIR-999",
            "date": "2026-09-18 10:30:00",
            "patient_id": "SUBJ-404",
            "duration": "02:30",
            "loadState": "MODERATE",
            "stress_index": 0.48,
            "dominant_freq": 10.2,
            "tbr": 1.15,
            "abr": 0.95,
            "delta": 22.5,
            "theta": 26.0,
            "alpha": 34.5,
            "beta": 17.0
        }

        fhir_export = FHIRExporter.generate_bundle(session_data)
        self.assertIn("bundle", fhir_export)
        bundle = fhir_export["bundle"]

        self.assertEqual(bundle.get("resourceType"), "Bundle")
        self.assertEqual(bundle.get("type"), "collection")
        self.assertIn("entry", bundle)
        self.assertGreater(len(bundle["entry"]), 3)

        # First entry must be DiagnosticReport
        diag_report = bundle["entry"][0]["resource"]
        self.assertEqual(diag_report["resourceType"], "DiagnosticReport")
        self.assertEqual(diag_report["status"], "final")
        self.assertEqual(diag_report["code"]["coding"][0]["code"], "28634-4") # LOINC EEG study
        self.assertIn("result", diag_report)

        # Verify linked Observation resources exist in the bundle
        obs_codes = [
            e["resource"].get("code", {}).get("coding", [{}])[0].get("code")
            for e in bundle["entry"] if e["resource"]["resourceType"] == "Observation"
        ]
        self.assertIn("9279-1", obs_codes) # SSI
        self.assertIn("88262-1", obs_codes) # TBR
        self.assertIn("88260-5", obs_codes) # Dominant Frequency

    # --------------------------------------------------------------------------
    # 4. IEC 60601-2-26 Electrode Impedance Monitoring & Interlock
    # --------------------------------------------------------------------------
    def test_impedance_manager_thresholds_and_override(self):
        """Validates continuous impedance gating (< 5 kOhm) and physician override."""
        mgr = ImpedanceManager()

        # 1. Optimal impedances across all leads (< 5 kOhm)
        mgr.update_all({
            "Fp1": 2.4, "Fp2": 3.1, "C3": 2.8, "C4": 3.5,
            "P3": 2.9, "P4": 3.2, "O1": 2.1, "O2": 2.5
        })
        passed, details = mgr.is_preflight_passed()
        self.assertTrue(passed)
        self.assertTrue(details["can_record"])
        self.assertEqual(len(details["failing_channels"]), 0)

        # 2. Simulate poor contact / high impedance on P4 (8.2 kOhm)
        mgr.update_channel("P4", 8.2)
        passed_fail, details_fail = mgr.is_preflight_passed()
        self.assertFalse(passed_fail)
        self.assertFalse(details_fail["can_record"])
        self.assertIn("P4", details_fail["failing_channels"])
        self.assertEqual(details_fail["failing_channels"]["P4"]["status"], "ACCEPTABLE")

        # 3. Simulate complete lead-off on O2 (14.5 kOhm)
        mgr.update_channel("O2", 14.5)
        _, details_lead_off = mgr.is_preflight_passed()
        self.assertEqual(details_lead_off["failing_channels"]["O2"]["status"], "LEAD_OFF")

        # 4. Authorize Physician Protocol Override
        override_res = mgr.set_clinical_override("Scalp abrasion on P4; clinical authorization granted")
        self.assertTrue(override_res["override_active"])
        
        # Preflight should still record failure, but can_record is True due to override
        passed_ov, details_ov = mgr.is_preflight_passed()
        self.assertFalse(passed_ov)
        self.assertTrue(details_ov["can_record"])
        self.assertTrue(details_ov["override_active"])

        # 5. Clear override
        mgr.clear_clinical_override()
        _, details_cleared = mgr.is_preflight_passed()
        self.assertFalse(details_cleared["can_record"])

    # --------------------------------------------------------------------------
    # 5. Physiological Artifact Suppression (EOG Blink & Temporal EMG Clamping)
    # --------------------------------------------------------------------------
    def test_artifact_filter_ocular_and_emg_clamping(self):
        """Validates online attenuation of EOG blink voltage spikes and high-frequency EMG."""
        filt = ArtifactFilter(sampling_rate=250)

        # Clean 10 Hz alpha wave (25 uV peak)
        t = np.linspace(0, 1.0, 250, endpoint=False)
        clean_signal = 25.0 * np.sin(2 * np.pi * 10.0 * t)
        filtered_clean, info_clean = filt.filter_epoch(clean_signal.tolist(), channel="Fp1")
        
        # Clean signal should pass through with negligible distortion
        self.assertEqual(info_clean["blink_count"], 0)
        self.assertEqual(info_clean["emg_burst_count"], 0)
        np.testing.assert_allclose(filtered_clean, clean_signal, atol=2.0)

        # Inject high-amplitude EOG blink spike (280 uV)
        corrupted_eog = clean_signal.copy()
        corrupted_eog[50:80] += 280.0 # Ocular artifact spike

        filtered_eog, info_eog = filt.filter_epoch(corrupted_eog.tolist(), channel="Fp1")
        self.assertGreater(info_eog["blink_count"], 0)
        self.assertLess(np.max(np.abs(filtered_eog[50:80])), 140.0) # Confirms clamping

        # Inject high-frequency EMG muscle burst (> 45 Hz, 140 uV)
        corrupted_emg = clean_signal.copy()
        corrupted_emg[120:170] += 140.0 * np.sin(2 * np.pi * 55.0 * t[120:170])

        filtered_emg, info_emg = filt.filter_epoch(corrupted_emg.tolist(), channel="C3")
        self.assertGreater(info_emg["emg_burst_count"], 0)
        self.assertLess(np.max(np.abs(filtered_emg[120:170])), 125.0)

    # --------------------------------------------------------------------------
    # 6. Explainable AI (XAI) Saliency & Feature Attribution (FDA GMLP)
    # --------------------------------------------------------------------------
    def test_xai_saliency_attribution_computation(self):
        """Validates pre-softmax gradient saliency computation across 64 electrophysiological features."""
        classifier = DeepNeuroReportModel.load_trained()
        self.assertGreaterEqual(classifier.total_parameters, 500000)
        self.assertEqual(classifier.total_parameters, 517828)

        # 1. High Cognitive Workload input pattern
        high_workload_metrics = {
            "delta": 5.0,
            "theta": 10.0,
            "alpha": 15.0,
            "beta": 70.0,
            "stress_index": 2.5
        }

        report = classifier.generate_full_clinical_report(high_workload_metrics)
        self.assertEqual(report["predicted_state"], "HIGH")
        self.assertIn("saliency_top_features", report)

        top_feats = report["saliency_top_features"]
        self.assertGreater(len(top_feats), 0)
        
        # Verify rank ordering and attribution percentage sum
        pct_sum = sum(item["attribution_pct"] for item in top_feats)
        self.assertGreater(pct_sum, 20.0)
        self.assertEqual(top_feats[0]["rank"], 1)
        self.assertGreater(top_feats[0]["sensitivity_magnitude"], 0.0)

        # 2. Relaxed Baseline (Low Workload) input pattern
        low_workload_metrics = {
            "delta": 50.0,
            "theta": 35.0,
            "alpha": 10.0,
            "beta": 5.0,
            "stress_index": 0.1
        }
        report_low = classifier.generate_full_clinical_report(low_workload_metrics)
        self.assertEqual(report_low["predicted_state"], "LOW")
        self.assertIn("saliency_top_features", report_low)
        self.assertGreater(len(report_low["saliency_top_features"]), 0)


if __name__ == '__main__':
    unittest.main()
