"""
Unit Tests — SQLite Database Manager
Tests saving, loading, and deleting session history records.
"""

import os
import unittest
import tempfile
from src.database.db_manager import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.tmp_db.close()
        self.db = DatabaseManager(db_path=self.tmp_db.name)

    def tearDown(self):
        if os.path.exists(self.tmp_db.name):
            try:
                os.remove(self.tmp_db.name)
            except OSError:
                pass

    def test_save_and_retrieve_session(self):
        session_data = {
            'session_id': 'TEST-SESS-001',
            'timestamp': '2026-07-28 10:00:00',
            'duration': 120.5,
            'sampling_rate': 250,
            'mode': 'SIMULATION',
            'rel_delta': 10.0,
            'rel_theta': 20.0,
            'rel_alpha': 50.0,
            'rel_beta': 20.0,
            'dominant_band': 'ALPHA',
            'cognitive_state': 'MODERATE',
            'stress_index': 0.5,
            'confidence': 90.0,
            'notes': 'Test Recording'
        }
        saved = self.db.save_session(session_data)
        self.assertTrue(saved)

        fetched = self.db.get_session_by_id('TEST-SESS-001')
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched['dominant_band'], 'ALPHA')
        self.assertEqual(fetched['cognitive_state'], 'MODERATE')

    def test_delete_session(self):
        session_data = {
            'session_id': 'TEST-SESS-002',
            'timestamp': '2026-07-28 11:00:00',
            'duration': 60.0,
            'sampling_rate': 250,
            'mode': 'HARDWARE',
            'rel_delta': 25.0,
            'rel_theta': 25.0,
            'rel_alpha': 25.0,
            'rel_beta': 25.0,
            'dominant_band': 'BETA',
            'cognitive_state': 'HIGH',
            'stress_index': 1.0,
            'confidence': 85.0
        }
        self.db.save_session(session_data)
        deleted = self.db.delete_session('TEST-SESS-002')
        self.assertTrue(deleted)
        self.assertIsNone(self.db.get_session_by_id('TEST-SESS-002'))

if __name__ == '__main__':
    unittest.main()
