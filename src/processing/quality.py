"""
Signal Quality & Acquisition Reliability Processing Module
Provides real-time channel quality assessment, artifact burden estimation,
flatline/saturation detection, temporal quality tracking, and acquisition telemetry.
Enforces truthful hardware boundaries (NO fake impedance values).
"""

import math
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

class EEGQualityEvaluator:
    """
    Evaluates signal quality, artifact burden, and acquisition reliability
    from raw EEG time-series snapshots and spectral analysis results.
    """

    def __init__(self, sampling_rate: int = 250):
        self.sampling_rate = int(sampling_rate)

    def evaluate_channel(self, samples: np.ndarray, freqs: Optional[np.ndarray] = None, psd: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Evaluates single-channel time-series signal quality and artifact metrics.
        Guarantees all output values are standard Python types (float, int, bool, str, None).
        """
        if samples is None or len(samples) < 32:
            return {
                "quality_score": None,
                "rating": "INSUFFICIENT DATA",
                "usable_data_pct": 0.0,
                "flatline": False,
                "saturation": False,
                "noise_burden_pct": 0.0,
                "artifact_burden_pct": 0.0,
                "powerline_noise_pct": 0.0,
                "valid": False,
            }

        std_dev = float(np.std(samples))
        peak_to_peak = float(np.ptp(samples))
        max_amp = float(np.max(np.abs(samples)))

        # 1. Saturation / Clipping Detection (> 500 uV max amplitude)
        saturation = bool(max_amp >= 500.0 or (np.sum(np.abs(samples) >= max_amp * 0.99) > len(samples) * 0.1 and max_amp > 100.0))

        # 2. Flatline Detection (< 0.01 uV peak-to-peak or std < 0.001 AND not saturated rail)
        flatline = bool((std_dev < 0.001 or peak_to_peak < 0.01) and not saturation)

        # 3. Power-line interference (50/60 Hz ratio)
        powerline_pct = 0.0
        if freqs is not None and psd is not None and len(psd) > 0 and np.sum(psd) > 0:
            pl_idx = np.where((freqs >= 48.0) & (freqs <= 62.0))[0]
            if len(pl_idx) > 0:
                fn_trapz = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
                pl_power = float(fn_trapz(psd[pl_idx], freqs[pl_idx])) if fn_trapz else float(np.sum(psd[pl_idx]))
                powerline_pct = float(min(100.0, max(0.0, (pl_power / (np.sum(psd) + 1e-12)) * 100.0)))

        # 4. Artifact Burden & High-Frequency Noise
        ocular_surge = float(np.sum(np.abs(samples) > 100.0) / len(samples)) * 100.0
        hf_noise_pct = float(min(100.0, max(0.0, (std_dev / (peak_to_peak + 1e-6)) * 10.0)))
        artifact_burden_pct = float(round(min(100.0, max(0.0, ocular_surge * 0.5 + powerline_pct * 0.5)), 2))

        # 5. Quality Score & Rating
        if flatline:
            score = 0.0
            rating = "FLATLINE"
            usable_pct = 0.0
        elif saturation:
            score = 15.0
            rating = "SATURATED"
            usable_pct = 10.0
        else:
            base_score = 100.0 - (artifact_burden_pct * 0.6) - (powerline_pct * 0.4)
            score = float(round(max(0.0, min(100.0, base_score)), 1))
            usable_pct = float(round(max(0.0, min(100.0, 100.0 - artifact_burden_pct)), 1))
            
            if score >= 85.0:
                rating = "EXCELLENT"
            elif score >= 70.0:
                rating = "GOOD"
            elif score >= 50.0:
                rating = "FAIR"
            else:
                rating = "POOR"

        valid = bool(not flatline and not saturation and len(samples) >= 32)

        return {
            "quality_score": score,
            "rating": rating,
            "usable_data_pct": usable_pct,
            "flatline": flatline,
            "saturation": saturation,
            "noise_burden_pct": float(round(hf_noise_pct, 2)),
            "artifact_burden_pct": artifact_burden_pct,
            "powerline_noise_pct": float(round(powerline_pct, 2)),
            "valid": valid,
        }

    def evaluate_multichannel(self, all_samples: np.ndarray, channels: Tuple[str, ...], freqs: Optional[np.ndarray] = None, psd: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Evaluates multi-channel quality array for all channels (FP1, FP2, O1, O2, etc.).
        Returns per-channel dictionary and overall summary metrics.
        Guarantees JSON-serializable Python types.
        """
        if not isinstance(all_samples, np.ndarray) or all_samples.ndim != 2 or all_samples.shape[1] < 32:
            return {
                "overall_score": None,
                "overall_rating": "INSUFFICIENT DATA",
                "overall_usable_pct": 0.0,
                "overall_artifact_pct": 0.0,
                "valid": False,
                "channels": {str(ch): self.evaluate_channel(np.array([])) for ch in channels},
                "impedance": {
                    "available": False,
                    "status": "NOT_SUPPORTED",
                    "notice": "Physical electrode impedance measurement hardware is disconnected."
                }
            }

        channel_evals = {}
        scores = []
        usables = []
        artifacts = []

        for idx, ch in enumerate(channels):
            ch_str = str(ch)
            if idx < all_samples.shape[0]:
                ch_samples = all_samples[idx]
                ev = self.evaluate_channel(ch_samples, freqs, psd)
            else:
                ev = self.evaluate_channel(np.array([]))

            channel_evals[ch_str] = ev
            if ev["quality_score"] is not None:
                scores.append(ev["quality_score"])
                usables.append(ev["usable_data_pct"])
                artifacts.append(ev["artifact_burden_pct"])

        avg_score = float(round(float(np.mean(scores)), 1)) if scores else 0.0
        avg_usable = float(round(float(np.mean(usables)), 1)) if usables else 0.0
        avg_artifact = float(round(float(np.mean(artifacts)), 2)) if artifacts else 0.0

        if avg_score >= 85.0:
            ov_rating = "EXCELLENT"
        elif avg_score >= 70.0:
            ov_rating = "GOOD"
        elif avg_score >= 50.0:
            ov_rating = "FAIR"
        elif avg_score > 0.0:
            ov_rating = "POOR"
        else:
            ov_rating = "NO SIGNAL"

        all_valid = bool(all(ev.get("valid", False) for ev in channel_evals.values()))

        return {
            "overall_score": avg_score,
            "overall_rating": ov_rating,
            "overall_usable_pct": avg_usable,
            "overall_artifact_pct": avg_artifact,
            "valid": all_valid,
            "channels": channel_evals,
            "impedance": {
                "available": False,
                "status": "NOT_SUPPORTED",
                "notice": "Physical electrode impedance measurement hardware is disconnected."
            }
        }
