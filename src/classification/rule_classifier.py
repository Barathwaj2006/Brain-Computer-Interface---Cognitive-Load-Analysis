"""
Rule-Based Cognitive Load & Stress Classifier
Evaluates signal features (relative band powers, band ratios, stress index) to classify
synthetic EEG patterns into LOW, MODERATE, or HIGH cognitive workload/stress states.
"""

from typing import Dict, Any

class RuleBasedClassifier:
    def classify(self, psd_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify synthetic EEG features using clinical rules.
        Returns:
            cognitive_state (str): 'LOW', 'MODERATE', or 'HIGH'
            confidence (float): Percentage confidence (0-100%)
            stress_level (str): 'RELAXED', 'BALANCED', or 'HIGH STRESS'
            signal_quality (str): 'EXCELLENT', 'GOOD', 'FAIR', or 'POOR'
            description (str): Clinical state interpretation
        """
        rel = psd_metrics.get('rel_powers', {'delta': 25.0, 'theta': 25.0, 'alpha': 25.0, 'beta': 25.0})
        
        d = rel.get('delta', 25.0)
        t = rel.get('theta', 25.0)
        a = rel.get('alpha', 25.0)
        b = rel.get('beta', 25.0)

        stress_index = psd_metrics.get('stress_index', 0.5)
        tbr = psd_metrics.get('theta_beta_ratio', 1.0)
        total_p = psd_metrics.get('total_power', 1.0)

        # Classification decision boundaries
        if b >= 35.0 or stress_index >= 0.8:
            cognitive_state = 'HIGH'
            stress_level = 'HIGH STRESS'
            base_confidence = min(98.0, 75.0 + (b - 35.0) * 0.8)
            description = "High beta synchrony detected. Indicates active problem-solving, cognitive stress, or heightened focus."
        elif a >= 35.0 or (a >= 30.0 and b < 30.0):
            cognitive_state = 'MODERATE'
            stress_level = 'BALANCED'
            base_confidence = min(98.0, 75.0 + (a - 30.0) * 0.8)
            description = "Prominent alpha rhythm observed. Characteristic of relaxed alertness, calm mental focus, or idle baseline."
        else:
            cognitive_state = 'LOW'
            stress_level = 'RELAXED'
            dominant_low = max(d, t)
            base_confidence = min(98.0, 75.0 + (dominant_low - 25.0) * 0.8)
            description = "Elevated delta/theta power dominant. Associated with deep relaxation, drowsiness, or low cognitive demand."

        # Signal Quality Assessment
        if total_p < 1e-4:
            signal_quality = 'POOR'
        elif total_p > 1e6:
            signal_quality = 'FAIR (ARTIFACT)'
        else:
            signal_quality = 'EXCELLENT'

        return {
            'cognitive_state': cognitive_state,
            'confidence': round(max(60.0, base_confidence), 1),
            'stress_level': stress_level,
            'signal_quality': signal_quality,
            'description': description
        }
