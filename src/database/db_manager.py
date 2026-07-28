"""
SQLite Database Storage Module
Stores and manages recorded EEG cognitive analysis sessions, band powers, stress metrics, and timestamps.
"""

import os
import sqlite3
import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "neurosim_history.db")

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Initialize sessions table schema."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                duration REAL NOT NULL,
                sampling_rate INTEGER NOT NULL,
                mode TEXT NOT NULL,
                rel_delta REAL NOT NULL,
                rel_theta REAL NOT NULL,
                rel_alpha REAL NOT NULL,
                rel_beta REAL NOT NULL,
                dominant_band TEXT NOT NULL,
                cognitive_state TEXT NOT NULL,
                stress_index REAL NOT NULL,
                confidence REAL NOT NULL,
                notes TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save_session(self, session_data: Dict[str, Any]) -> bool:
        """Save a completed session record to database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sessions (
                    session_id, timestamp, duration, sampling_rate, mode,
                    rel_delta, rel_theta, rel_alpha, rel_beta,
                    dominant_band, cognitive_state, stress_index, confidence, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_data['session_id'],
                session_data.get('timestamp', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                float(session_data.get('duration', 0.0)),
                int(session_data.get('sampling_rate', 250)),
                session_data.get('mode', 'SIMULATION'),
                float(session_data.get('rel_delta', 25.0)),
                float(session_data.get('rel_theta', 25.0)),
                float(session_data.get('rel_alpha', 25.0)),
                float(session_data.get('rel_beta', 25.0)),
                session_data.get('dominant_band', 'ALPHA'),
                session_data.get('cognitive_state', 'MODERATE'),
                float(session_data.get('stress_index', 0.5)),
                float(session_data.get('confidence', 85.0)),
                session_data.get('notes', 'Synthetic EEG Recording')
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
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        sessions = [dict(row) for row in rows]
        conn.close()
        return sessions

    def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific session record by session_id."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[DB Error] Failed to delete session: {e}")
            return False
