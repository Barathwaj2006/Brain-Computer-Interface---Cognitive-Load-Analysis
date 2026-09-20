import unittest
import time
import os
import sqlite3
from server import DatabaseManager, parse_telemetry_packet

class TestEventMarkersAndTelemetry(unittest.TestCase):
    def setUp(self):
        DatabaseManager.init_db()

    def test_insert_and_get_markers(self):
        uid = f"TEST-SES-{int(time.time()*1000)}"
        
        # Insert marker 1
        m1_id = DatabaseManager.insert_marker(
            session_uid=uid,
            label="Eyes Closed",
            sample_index=250,
            timestamp=time.time(),
            notes="Subject instructed to close eyes"
        )
        self.assertIsNotNone(m1_id)

        # Insert marker 2
        m2_id = DatabaseManager.insert_marker(
            session_uid=uid,
            label="Eyes Open",
            sample_index=1750,
            timestamp=time.time(),
            notes="Subject opened eyes, looking at fixation point"
        )
        self.assertIsNotNone(m2_id)

        # Retrieve markers
        markers = DatabaseManager.get_markers(uid)
        self.assertEqual(len(markers), 2)
        self.assertEqual(markers[0]["marker_label"], "Eyes Closed")
        self.assertEqual(markers[0]["sample_index"], 250)
        self.assertEqual(markers[1]["marker_label"], "Eyes Open")
        self.assertEqual(markers[1]["sample_index"], 1750)

    def test_multi_sample_batch_parsing(self):
        # Test batched multi-sample line parsing
        line = "SAMPLE,14.5,2.1,0.0,512.0,101,OK"
        parsed = parse_telemetry_packet(line)
        self.assertIsNotNone(parsed)
        val, e1, e2, e3, sensor, seq, chk_ok = parsed
        self.assertAlmostEqual(e1, 14.5)
        self.assertAlmostEqual(e2, 2.1)
        self.assertAlmostEqual(val, 12.4)
        self.assertAlmostEqual(sensor, 512.0)
        self.assertEqual(seq, 101)
        self.assertTrue(chk_ok)

if __name__ == '__main__':
    unittest.main()
