"""
Feature Extraction Module
Converts PSD spectral metrics into feature vectors for Cognitive Load & Stress Classifiers.
"""

import numpy as np
from typing import Dict, Any, List

class EEGFeatureExtractor:
    @staticmethod
    def extract_features(psd_metrics: Dict[str, Any]) -> List[float]:
        """
        Extract numerical feature vector from PSD analysis metrics.
        Features:
        [0] Rel Delta %
        [1] Rel Theta %
        [2] Rel Alpha %
        [3] Rel Beta %
        [4] Theta / Beta Ratio
        [5] Alpha / Beta Ratio
        [6] Stress Index (Beta / (Alpha + Theta))
        [7] Total Power (log scale)
        """
        rel = psd_metrics.get('rel_powers', {'delta': 25.0, 'theta': 25.0, 'alpha': 25.0, 'beta': 25.0})
        
        rel_delta = float(rel.get('delta', 25.0))
        rel_theta = float(rel.get('theta', 25.0))
        rel_alpha = float(rel.get('alpha', 25.0))
        rel_beta  = float(rel.get('beta', 25.0))

        tbr = float(psd_metrics.get('theta_beta_ratio', 1.0))
        abr = float(psd_metrics.get('alpha_beta_ratio', 1.0))
        stress = float(psd_metrics.get('stress_index', 0.5))
        total_p = np.log10(max(1e-6, float(psd_metrics.get('total_power', 1.0))))

        return [rel_delta, rel_theta, rel_alpha, rel_beta, tbr, abr, stress, total_p]

    @staticmethod
    def feature_names() -> List[str]:
        return [
            'rel_delta', 'rel_theta', 'rel_alpha', 'rel_beta',
            'theta_beta_ratio', 'alpha_beta_ratio', 'stress_index', 'log_total_power'
        ]
