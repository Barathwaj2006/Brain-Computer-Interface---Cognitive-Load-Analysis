"""
SQLite Database Storage Module — NeuroSim 2.0
Stores and manages recorded EEG cognitive analysis sessions, band powers, stress metrics, and timestamps.
Enhanced with session comparison, historical analysis, and longitudinal trend support.
"""

import os
import sqlite3
import datetime
import json
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "neurosim_history.db")


class DatabaseManager:
    """
    Enhanced database manager for session persistence, retrieval, comparison, and historical analysis.
    """
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize sessions table schema with extended fields for research."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Main sessions table with comprehensive metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                duration REAL NOT NULL,
                sampling_rate INTEGER NOT NULL,
                source TEXT NOT NULL,
                channel_count INTEGER DEFAULT 8,
                sample_count INTEGER DEFAULT 0,
                rel_delta REAL NOT NULL,
                rel_theta REAL NOT NULL,
                rel_alpha REAL NOT NULL,
                rel_beta REAL NOT NULL,
                abs_delta REAL DEFAULT 0.0,
                abs_theta REAL DEFAULT 0.0,
                abs_alpha REAL DEFAULT 0.0,
                abs_beta REAL DEFAULT 0.0,
                total_power REAL DEFAULT 0.0,
                dominant_band TEXT NOT NULL,
                dominant_frequency REAL DEFAULT 10.0,
                cognitive_state TEXT NOT NULL,
                stress_index REAL NOT NULL,
                confidence REAL NOT NULL,
                tbr REAL DEFAULT 0.0,
                abr REAL DEFAULT 0.0,
                signal_quality REAL DEFAULT 85.0,
                noise_level REAL DEFAULT 15.0,
                artifact_rate REAL DEFAULT 5.0,
                snr_db REAL DEFAULT 20.0,
                notes TEXT,
                user_id TEXT DEFAULT 'anonymous',
                protocol_name TEXT DEFAULT 'standard',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Session events table for granular timeline data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                event_timestamp REAL NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        
        # Create indices for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_timestamp ON sessions(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_state ON sessions(cognitive_state)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON session_events(session_id)")
        
        conn.commit()
        conn.close()

    def save_session(self, session_data: Dict[str, Any]) -> bool:
        """Save a completed session record to database with comprehensive metadata."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Calculate derived metrics if not provided
            delta = float(session_data.get('abs_delta', session_data.get('delta', session_data.get('rel_delta', 25.0))))
            theta = float(session_data.get('abs_theta', session_data.get('theta', session_data.get('rel_theta', 25.0))))
            alpha = float(session_data.get('abs_alpha', session_data.get('alpha', session_data.get('rel_alpha', 25.0))))
            beta = float(session_data.get('abs_beta', session_data.get('beta', session_data.get('rel_beta', 25.0))))
            total_power = delta + theta + alpha + beta
            
            if total_power > 0 and session_data.get('rel_delta') is None:
                rel_delta = (delta / total_power) * 100
                rel_theta = (theta / total_power) * 100
                rel_alpha = (alpha / total_power) * 100
                rel_beta = (beta / total_power) * 100
            else:
                rel_delta = float(session_data.get('rel_delta', 25.0))
                rel_theta = float(session_data.get('rel_theta', 25.0))
                rel_alpha = float(session_data.get('rel_alpha', 25.0))
                rel_beta = float(session_data.get('rel_beta', 25.0))
            
            # Calculate ratios
            tbr = theta / beta if beta > 0 else 0.0
            abr = alpha / beta if beta > 0 else 0.0
            
            cursor.execute("""
                INSERT OR REPLACE INTO sessions (
                    session_id, timestamp, duration, sampling_rate, source, channel_count, sample_count,
                    rel_delta, rel_theta, rel_alpha, rel_beta,
                    abs_delta, abs_theta, abs_alpha, abs_beta, total_power,
                    dominant_band, dominant_frequency, cognitive_state, stress_index, 
                    confidence, tbr, abr, signal_quality, noise_level, artifact_rate, snr_db,
                    notes, user_id, protocol_name, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_data['session_id'],
                session_data.get('timestamp', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                float(session_data.get('duration', 0.0)),
                int(session_data.get('sampling_rate', 250)),
                session_data.get('source', session_data.get('mode', 'SIMULATION')),
                int(session_data.get('channel_count', 8)),
                int(session_data.get('sample_count', 0)),
                rel_delta, rel_theta, rel_alpha, rel_beta,
                delta, theta, alpha, beta, total_power,
                session_data.get('dominant_band', 'ALPHA'),
                float(session_data.get('dominant_frequency', 10.0)),
                session_data.get('cognitive_state', 'MODERATE'),
                float(session_data.get('stress_index', 0.5)),
                float(session_data.get('confidence', 85.0)),
                session_data.get('tbr', tbr),
                session_data.get('abr', abr),
                float(session_data.get('signal_quality', 85.0)),
                float(session_data.get('noise_level', 15.0)),
                float(session_data.get('artifact_rate', 5.0)),
                float(session_data.get('snr_db', session_data.get('snr', 20.0))),
                session_data.get('notes', 'EEG Recording Session'),
                session_data.get('user_id', 'anonymous'),
                session_data.get('protocol_name', 'standard'),
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[DB Error] Failed to save session: {e}")
            return False

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Retrieve all recorded sessions sorted by timestamp descending."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        sessions = [dict(row) for row in rows]
        conn.close()
        return sessions

    def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific session record by session_id."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_sessions_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve all sessions for a specific user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        rows = cursor.fetchall()
        sessions = [dict(row) for row in rows]
        conn.close()
        return sessions

    def get_sessions_by_date_range(self, start_date: str, end_date: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve sessions within a date range for longitudinal analysis."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute(
                "SELECT * FROM sessions WHERE timestamp BETWEEN ? AND ? AND user_id = ? ORDER BY timestamp ASC",
                (start_date, end_date, user_id)
            )
        else:
            cursor.execute(
                "SELECT * FROM sessions WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp ASC",
                (start_date, end_date)
            )
        
        rows = cursor.fetchall()
        sessions = [dict(row) for row in rows]
        conn.close()
        return sessions

    def get_sessions_by_cognitive_state(self, state: str) -> List[Dict[str, Any]]:
        """Retrieve sessions filtered by cognitive state classification."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE cognitive_state = ? ORDER BY timestamp DESC", (state,))
        rows = cursor.fetchall()
        sessions = [dict(row) for row in rows]
        conn.close()
        return sessions

    def compare_sessions(self, session_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple sessions and return comparative statistics."""
        sessions = [self.get_session_by_id(sid) for sid in session_ids if self.get_session_by_id(sid)]
        
        if len(sessions) < 2:
            return {'error': 'Need at least 2 sessions for comparison', 'sessions': sessions}
        
        comparison = {
            'session_count': len(sessions),
            'session_ids': session_ids,
            'metrics': {}
        }
        
        # Compare key metrics across sessions
        metric_keys = ['rel_delta', 'rel_theta', 'rel_alpha', 'rel_beta', 'stress_index', 
                       'confidence', 'signal_quality', 'tbr', 'abr', 'dominant_frequency']
        
        for metric in metric_keys:
            values = [s.get(metric, 0) for s in sessions if s.get(metric) is not None]
            if values:
                comparison['metrics'][metric] = {
                    'min': min(values),
                    'max': max(values),
                    'mean': sum(values) / len(values),
                    'range': max(values) - min(values),
                    'values': values
                }
        
        # Cognitive state distribution
        state_counts = defaultdict(int)
        for s in sessions:
            state_counts[s.get('cognitive_state', 'UNKNOWN')] += 1
        comparison['cognitive_state_distribution'] = dict(state_counts)
        
        return comparison

    def get_longitudinal_trends(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze longitudinal trends for a user over specified days."""
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        sessions = self.get_sessions_by_date_range(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            user_id
        )
        
        if len(sessions) < 2:
            return {'error': 'Insufficient sessions for trend analysis', 'session_count': len(sessions)}
        
        trends = {
            'user_id': user_id,
            'period_days': days,
            'session_count': len(sessions),
            'band_power_trends': {},
            'stress_trend': [],
            'quality_trend': [],
            'cognitive_state_sequence': []
        }
        
        # Extract time series data
        for sess in sessions:
            trends['stress_trend'].append({
                'timestamp': sess['timestamp'],
                'value': sess.get('stress_index', 0.5)
            })
            trends['quality_trend'].append({
                'timestamp': sess['timestamp'],
                'value': sess.get('signal_quality', 85.0)
            })
            trends['cognitive_state_sequence'].append(sess.get('cognitive_state', 'UNKNOWN'))
        
        # Calculate band power trends
        for band in ['rel_delta', 'rel_theta', 'rel_alpha', 'rel_beta']:
            values = [s.get(band, 0) for s in sessions]
            if len(values) >= 2:
                # Simple linear trend calculation
                n = len(values)
                x_mean = (n - 1) / 2
                y_mean = sum(values) / n
                
                numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
                denominator = sum((i - x_mean) ** 2 for i in range(n))
                
                slope = numerator / denominator if denominator != 0 else 0
                
                trends['band_power_trends'][band] = {
                    'values': values,
                    'mean': y_mean,
                    'slope': slope,
                    'trend_direction': 'increasing' if slope > 0.1 else 'decreasing' if slope < -0.1 else 'stable'
                }
        
        return trends

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM session_events WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[DB Error] Failed to delete session: {e}")
            return False

    def save_session_event(self, session_id: str, event_type: str, event_data: Optional[Dict] = None, timestamp: Optional[float] = None) -> bool:
        """Save an event within a session timeline."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO session_events (session_id, event_timestamp, event_type, event_data)
                VALUES (?, ?, ?, ?)
            """, (
                session_id,
                timestamp if timestamp is not None else datetime.datetime.now().timestamp(),
                event_type,
                json.dumps(event_data) if event_data else None
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[DB Error] Failed to save event: {e}")
            return False

    def get_session_events(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all events for a session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM session_events WHERE session_id = ? ORDER BY event_timestamp ASC", (session_id,))
        rows = cursor.fetchall()
        events = []
        for row in rows:
            event = dict(row)
            if event.get('event_data'):
                event['event_data'] = json.loads(event['event_data'])
            events.append(event)
        conn.close()
        return events

    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get overall database statistics."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total sessions
        cursor.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = cursor.fetchone()[0]
        
        # Sessions by cognitive state
        cursor.execute("SELECT cognitive_state, COUNT(*) FROM sessions GROUP BY cognitive_state")
        state_dist = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Average metrics
        cursor.execute("""
            SELECT AVG(stress_index), AVG(signal_quality), AVG(confidence),
                   AVG(rel_alpha), AVG(rel_beta), AVG(rel_theta), AVG(rel_delta)
            FROM sessions
        """)
        avg_row = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_sessions': total_sessions,
            'cognitive_state_distribution': state_dist,
            'averages': {
                'stress_index': avg_row[0] or 0.5,
                'signal_quality': avg_row[1] or 85.0,
                'confidence': avg_row[2] or 85.0,
                'rel_alpha': avg_row[3] or 25.0,
                'rel_beta': avg_row[4] or 25.0,
                'rel_theta': avg_row[5] or 25.0,
                'rel_delta': avg_row[6] or 25.0,
            }
        }
