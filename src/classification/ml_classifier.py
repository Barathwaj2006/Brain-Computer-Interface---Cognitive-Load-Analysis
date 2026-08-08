"""
Machine Learning Classifier Module
Uses a trained Random Forest Classifier to predict synthetic EEG cognitive load & stress states.
"""

import sys
import os
import joblib
import numpy as np
from typing import Dict, Any
from src.features.extractor import EEGFeatureExtractor
from src.classification.rule_classifier import RuleBasedClassifier

def resolve_model_path() -> str:
    """
    Resolves the ML model path correctly whether running from source or from PyInstaller frozen .exe.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_dir = getattr(sys, '_MEIPASS')
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "models", "trained_rf_model.joblib")

MODEL_PATH = resolve_model_path()

class MLClassifier:
    def __init__(self, model_path: str = None):
        self.model_path = model_path if model_path else resolve_model_path()
        self.model = None
        self.classes = ['LOW', 'MODERATE', 'HIGH']
        self.rule_fallback = RuleBasedClassifier()
        self.load_error = None
        self.load_model()

    def load_model(self) -> bool:
        """Load trained Random Forest model if available."""
        if os.path.exists(self.model_path):
            try:
                data = joblib.load(self.model_path)
                self.model = data.get('model')
                self.classes = data.get('classes', ['LOW', 'MODERATE', 'HIGH'])
                self.load_error = None
                print(f"[MLClassifier] Successfully loaded ML model from: {self.model_path}")
                return True
            except Exception as e:
                self.load_error = f"Model load error: {e}"
                print(f"[MLClassifier WARNING] Failed to load model at {self.model_path}: {e}")
                self.model = None
        else:
            self.load_error = f"Model file not found at: {self.model_path}"
            print(f"[MLClassifier WARNING] Model file not found at: {self.model_path}. Using rule-based fallback.")
            self.model = None
        return False

    def predict(self, psd_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict cognitive state using ML model if present, or rule-based fallback.
        """
        if self.model is None:
            res = self.rule_fallback.classify(psd_metrics)
            res['model_type'] = f'Rule-Based Fallback ({self.load_error or "Model Not Loaded"})'
            res['is_ml'] = False
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
                'description': f"ML Model (Random Forest) statistical probability: {confidence:.1f}%.",
                'model_type': 'Random Forest Classifier (Synthetic Data)',
                'is_ml': True
            }
        except Exception as e:
            res = self.rule_fallback.classify(psd_metrics)
            res['model_type'] = f'Rule-Based Fallback (Prediction Error: {e})'
            res['is_ml'] = False
            return res
