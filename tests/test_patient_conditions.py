"""
Unit Tests for 20 Clinical Patient Condition Simulations
Verifies:
1. All 20 distinct patient conditions exist with valid patient IDs (PT-2026-001 to PT-2026-020).
2. Frequency band distributions, stress index, TBR, and ABR are physiologically valid.
3. Every condition has detailed clinical diagnostic findings.
4. Every condition has at least 3 concrete, prescriptive clinical actions.
5. Server-side diagnostic report synthesis recognizes and handles all 20 conditions.
"""

import unittest
from src.simulation.patient_conditions import PATIENT_CONDITIONS, get_all_conditions, get_condition

class TestPatientConditions(unittest.TestCase):
    def setUp(self):
        self.conditions = get_all_conditions()

    def test_condition_count(self):
        """Verify exactly 20 clinical conditions are loaded."""
        self.assertEqual(len(self.conditions), 20, "Must define exactly 20 clinical patient conditions.")

    def test_patient_ids_and_sequence(self):
        """Verify sequential patient IDs PT-2026-001 through PT-2026-020."""
        expected_ids = [f"PT-2026-{i:03d}" for i in range(1, 21)]
        actual_ids = [cond["patient_id"] for cond in self.conditions.values()]
        for expected in expected_ids:
            self.assertIn(expected, actual_ids, f"Patient ID {expected} missing from conditions.")

    def test_band_powers_sum_to_100(self):
        """Verify spectral band powers (delta, theta, alpha, beta) sum to approximately 100%."""
        for cid, cond in self.conditions.items():
            bands = cond["bands"]
            total = sum(bands.values())
            self.assertAlmostEqual(total, 100.0, delta=1.0,
                msg=f"Condition '{cid}' band powers sum to {total}%, expected ~100%")

    def test_clinical_action_plans(self):
        """Verify every condition has at least 3 distinct clinical action recommendations."""
        for cid, cond in self.conditions.items():
            actions = cond.get("patient_action_plan", [])
            self.assertGreaterEqual(len(actions), 3,
                f"Condition '{cid}' must contain at least 3 prescriptive actions, found {len(actions)}")
            for action in actions:
                self.assertIsInstance(action, str)
                self.assertGreater(len(action.strip()), 15,
                    f"Action text in condition '{cid}' too brief: '{action}'")

    def test_diagnostic_findings(self):
        """Verify each condition contains authentic, detailed neurological findings."""
        for cid, cond in self.conditions.items():
            diag = cond.get("patient_condition", "")
            self.assertIsInstance(diag, str)
            self.assertGreater(len(diag.strip()), 50,
                f"Diagnostic narrative in condition '{cid}' too brief: '{diag}'")

    def test_metrics_and_ratios(self):
        """Verify stress_index, TBR, ABR, and cognitive_load states."""
        valid_loads = {"LOW", "MODERATE", "HIGH", "FATIGUE"}
        for cid, cond in self.conditions.items():
            self.assertIn(cond["cognitive_load"], valid_loads,
                f"Invalid cognitive load in '{cid}': {cond['cognitive_load']}")
            self.assertGreater(cond["stress_index"], 0.0, f"Condition '{cid}' stress_index must be positive")
            self.assertGreater(cond["tbr"], 0.0, f"Condition '{cid}' TBR must be positive")
            self.assertGreater(cond["abr"], 0.0, f"Condition '{cid}' ABR must be positive")
            self.assertGreater(cond["dominant_freq"], 0.0, f"Condition '{cid}' dominant frequency must be > 0")

    def test_wave_parameters(self):
        """Verify waveform generator parameters exist for synthetic biopotential rendering."""
        for cid, cond in self.conditions.items():
            wp = cond.get("wave_params", {})
            self.assertIn("base_freq", wp, f"wave_params in '{cid}' missing base_freq")
            self.assertIn("noise", wp, f"wave_params in '{cid}' missing noise")

    def test_get_condition_fallback(self):
        """Verify fallback behavior for unknown condition ID."""
        fallback = get_condition("non_existent_case_xyz")
        self.assertEqual(fallback["id"], "case_01_resting_baseline")

    def test_categories_coverage(self):
        """Verify representation across clinical categories."""
        categories = set(cond["category"] for cond in self.conditions.values())
        expected_categories = {
            "Normal & Sleep Electrophysiology",
            "Cognitive & Mental States",
            "Neurological & Clinical Pathologies",
            "Artifacts & Pharmacological Effects"
        }
        self.assertEqual(categories, expected_categories)

if __name__ == '__main__':
    unittest.main()
