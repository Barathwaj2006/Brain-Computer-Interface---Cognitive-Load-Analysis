"""
Unit Tests — Cognitive Load & Stress Classifiers
Tests Rule-Based and Machine Learning classifiers on synthetic feature metrics.
"""

import unittest
from src.classification.rule_classifier import RuleBasedClassifier
from src.classification.ml_classifier import MLClassifier

class TestClassification(unittest.TestCase):
    def setUp(self):
        self.rule_clf = RuleBasedClassifier()
        self.ml_clf = MLClassifier()

    def test_rule_high_beta(self):
        metrics = {
            'rel_powers': {'delta': 10.0, 'theta': 10.0, 'alpha': 20.0, 'beta': 60.0},
            'stress_index': 1.2,
            'theta_beta_ratio': 0.16,
            'alpha_beta_ratio': 0.33,
            'total_power': 100.0
        }
        res = self.rule_clf.classify(metrics)
        self.assertEqual(res['cognitive_state'], 'HIGH')

    def test_rule_alpha_moderate(self):
        metrics = {
            'rel_powers': {'delta': 15.0, 'theta': 15.0, 'alpha': 55.0, 'beta': 15.0},
            'stress_index': 0.5,
            'theta_beta_ratio': 1.0,
            'alpha_beta_ratio': 3.6,
            'total_power': 100.0
        }
        res = self.rule_clf.classify(metrics)
        self.assertEqual(res['cognitive_state'], 'MODERATE')

    def test_ml_predict(self):
        metrics = {
            'rel_powers': {'delta': 15.0, 'theta': 15.0, 'alpha': 55.0, 'beta': 15.0},
            'stress_index': 0.5,
            'theta_beta_ratio': 1.0,
            'alpha_beta_ratio': 3.6,
            'total_power': 100.0
        }
        res = self.ml_clf.predict(metrics)
        self.assertIn('cognitive_state', res)
        self.assertIn(res['cognitive_state'], ['LOW', 'MODERATE', 'HIGH'])

if __name__ == '__main__':
    unittest.main()
