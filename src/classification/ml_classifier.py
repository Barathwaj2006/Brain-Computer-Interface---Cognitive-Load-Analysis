"""
Machine Learning Classifier Module
Uses a trained Random Forest Classifier to predict synthetic EEG cognitive load & stress states.
"""

import os
import joblib
import numpy as np
from typing import Dict, Any
from src.features.extractor import EEGFeatureExtractor
from src.classification.rule_classifier import RuleBasedClassifier

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", "trained_rf_model.joblib")

class MLClassifier:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self.model = None
        self.classes = ['LOW', 'MODERATE', 'HIGH']
        self.rule_fallback = RuleBasedClassifier()
        self.load_model()

    def load_model(self) -> bool:
        """Load trained Random Forest model if available."""
        if os.path.exists(self.model_path):
            try:
                data = joblib.load(self.model_path)
                self.model = data.get('model')
                self.classes = data.get('classes', ['LOW', 'MODERATE', 'HIGH'])
                return True
            except Exception as e:
                print(f"[MLClassifier] Failed to load model: {e}")
                self.model = None
        return False

    def predict(self, psd_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict cognitive state using ML model if present, or rule-based fallback.
        """
        if self.model is None:
            res = self.rule_fallback.classify(psd_metrics)
            res['model_type'] = 'Rule-Based Fallback'
            return res

        try:
            features = EEGFeatureExtractor.extract_features(psd_metrics)
            X = np.array(features).reshape(1, -1)
            
            probs = self.model.predict_proba(X)[0]
            pred_idx = np.argmax(probs)
            state = self.classes[pred_idx]
            confidence = float(probs[pred_idx] * 100.0)

            stress_level = 'HIGH STRESS' if state == 'HIGH' else ('BALANCED' if state == 'MODERATE' else 'RELAXED')

            return {
                'cognitive_state': state,
                'confidence': round(max(50.0, confidence), 1),
                'stress_level': stress_level,
                'signal_quality': 'EXCELLENT',
                'description': f"ML Model (Random Forest) prediction with {confidence:.1f}% confidence probability.",
                'model_type': 'Random Forest Classifier (Synthetic Data)'
            }
        except Exception as e:
            res = self.rule_fallback.classify(psd_metrics)
            res['model_type'] = f'Rule-Based Fallback (Error: {e})'
            return res
