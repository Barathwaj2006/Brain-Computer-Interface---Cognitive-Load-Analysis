"""
NeuroSim 3.0 Research Analytics Engine
Provides longitudinal session analytics, multi-session comparison matrices,
BIDS-compatible dataset exports, and research CSV summary exports.
"""

import csv
import io
import datetime
from typing import List, Dict, Any, Optional

from src.database.db_manager import DatabaseManager


class ResearchAnalyticsEngine:
    """
    Research Analytics Engine for NeuroSim 3.0.
    Computes cross-session trends, comparative matrices, and exports research datasets.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager()

    def get_longitudinal_summary(self) -> Dict[str, Any]:
        """Computes longitudinal cognitive load and spectral power trends over time."""
        sessions = self.db_manager.get_all_sessions()
        if not sessions:
            return {
                "total_sessions": 0,
                "total_duration_sec": 0.0,
                "avg_duration_sec": 0.0,
                "mean_stress_index": 0.0,
                "cognitive_state_counts": {},
                "dominant_band_counts": {},
                "timeline": []
            }

        total_sessions = len(sessions)
        total_duration = sum(float(s.get("duration", 0.0)) for s in sessions)
        avg_duration = total_duration / total_sessions if total_sessions > 0 else 0.0
        mean_stress = sum(float(s.get("stress_index", 0.0)) for s in sessions) / total_sessions

        state_counts: Dict[str, int] = {}
        band_counts: Dict[str, int] = {}
        timeline = []

        for s in reversed(sessions): # Oldest to newest
            state = s.get("cognitive_state", "MODERATE")
            band = s.get("dominant_band", "ALPHA")

            state_counts[state] = state_counts.get(state, 0) + 1
            band_counts[band] = band_counts.get(band, 0) + 1

            timeline.append({
                "session_id": s.get("session_id"),
                "timestamp": s.get("timestamp"),
                "duration": float(s.get("duration", 0.0)),
                "rel_delta": float(s.get("rel_delta", 25.0)),
                "rel_theta": float(s.get("rel_theta", 25.0)),
                "rel_alpha": float(s.get("rel_alpha", 25.0)),
                "rel_beta": float(s.get("rel_beta", 25.0)),
                "stress_index": float(s.get("stress_index", 0.5)),
                "cognitive_state": state,
                "dominant_band": band
            })

        return {
            "total_sessions": total_sessions,
            "total_duration_sec": total_duration,
            "avg_duration_sec": avg_duration,
            "mean_stress_index": round(mean_stress, 4),
            "cognitive_state_counts": state_counts,
            "dominant_band_counts": band_counts,
            "timeline": timeline
        }

    def compare_sessions(self, session_ids: List[str]) -> Dict[str, Any]:
        """Compares specific session records side-by-side."""
        if not session_ids:
            return {"compared_count": 0, "sessions": []}

        records = []
        for sid in session_ids:
            rec = self.db_manager.get_session_by_id(sid)
            if rec:
                records.append({
                    "session_id": rec.get("session_id"),
                    "timestamp": rec.get("timestamp"),
                    "duration": float(rec.get("duration", 0.0)),
                    "sampling_rate": int(rec.get("sampling_rate", 250)),
                    "mode": rec.get("mode"),
                    "rel_delta": float(rec.get("rel_delta", 25.0)),
                    "rel_theta": float(rec.get("rel_theta", 25.0)),
                    "rel_alpha": float(rec.get("rel_alpha", 25.0)),
                    "rel_beta": float(rec.get("rel_beta", 25.0)),
                    "dominant_band": rec.get("dominant_band"),
                    "cognitive_state": rec.get("cognitive_state"),
                    "stress_index": float(rec.get("stress_index", 0.5)),
                    "confidence": float(rec.get("confidence", 85.0))
                })

        return {
            "compared_count": len(records),
            "sessions": records
        }

    def export_csv_summary(self) -> str:
        """Generates CSV format text string of all recorded sessions for statistical packages."""
        sessions = self.db_manager.get_all_sessions()
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "session_id", "timestamp", "duration_sec", "sampling_rate_hz", "mode",
            "rel_delta_pct", "rel_theta_pct", "rel_alpha_pct", "rel_beta_pct",
            "dominant_band", "cognitive_state", "stress_index", "confidence_pct", "notes"
        ])

        for s in sessions:
            writer.writerow([
                s.get("session_id"),
                s.get("timestamp"),
                s.get("duration"),
                s.get("sampling_rate"),
                s.get("mode"),
                s.get("rel_delta"),
                s.get("rel_theta"),
                s.get("rel_alpha"),
                s.get("rel_beta"),
                s.get("dominant_band"),
                s.get("cognitive_state"),
                s.get("stress_index"),
                s.get("confidence"),
                s.get("notes")
            ])

        return output.getvalue()

    def export_bids_dataset(self) -> Dict[str, Any]:
        """Exports dataset structure compliant with BIDS (Brain Imaging Data Structure) EEG format."""
        sessions = self.db_manager.get_all_sessions()
        return {
            "BIDSVersion": "1.8.0",
            "DatasetType": "derivative",
            "Name": "NeuroSim Cognitive Analytics Dataset",
            "Authors": ["NeuroSim Research Group"],
            "DatasetDOI": "10.5281/zenodo.neurosim.v3.0",
            "GeneratedAt": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Sessions": [
                {
                    "sub": "001",
                    "ses": s.get("session_id"),
                    "task": "cognitiveload",
                    "datatype": "eeg",
                    "sampling_rate": s.get("sampling_rate"),
                    "duration": s.get("duration"),
                    "power_spectral_density": {
                        "delta": s.get("rel_delta"),
                        "theta": s.get("rel_theta"),
                        "alpha": s.get("rel_alpha"),
                        "beta": s.get("rel_beta")
                    },
                    "cognitive_metrics": {
                        "state": s.get("cognitive_state"),
                        "dominant_band": s.get("dominant_band"),
                        "stress_index": s.get("stress_index")
                    }
                } for s in sessions
            ]
        }
