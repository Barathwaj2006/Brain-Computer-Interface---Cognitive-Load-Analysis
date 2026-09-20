"""
Unit Tests for 3-Electrode + 1-Sensor Wi-Fi Hardware Telemetry Pipeline
Verifies that NeuroSim correctly ingests, parses, centers, and processes:
1. 4-channel CSV packets (e1, e2, e3, sensor)
2. 5-channel sequence packets (SAMPLE, e1, e2, e3, sensor, seq)
3. 2-channel differential + sensor packets (SAMPLE, eeg, sensor)
4. Raw ADC integer centering (>200 counts)
5. Differential EEG calculation (V_EEG = E1 - E2)
6. TelemetryState multi-channel tracking and export formats
"""

import unittest
import json
import time
from server import parse_telemetry_packet, TelemetryState

class TestThreeElectrodeStream(unittest.TestCase):
    def test_parse_four_channel_csv(self):
        """Test standard 4-channel CSV: e1, e2, e3, sensor"""
        line = "15.5, -2.5, 0.0, 512.0"
        val, e1, e2, e3, sensor, seq, chk = parse_telemetry_packet(line)
        self.assertAlmostEqual(e1, 15.5, places=2)
        self.assertAlmostEqual(e2, -2.5, places=2)
        self.assertAlmostEqual(e3, 0.0, places=2)
        self.assertAlmostEqual(sensor, 512.0, places=1)
        # Differential EEG: 15.5 - (-2.5) = 18.0
        self.assertAlmostEqual(val, 18.0, places=2)
        self.assertTrue(chk)

    def test_parse_sample_prefix_four_channel(self):
        """Test SAMPLE prefix with 4 channels: SAMPLE,e1,e2,e3,sensor"""
        line = "SAMPLE,22.0,5.0,0.0,1024.0"
        val, e1, e2, e3, sensor, seq, chk = parse_telemetry_packet(line)
        self.assertAlmostEqual(e1, 22.0, places=2)
        self.assertAlmostEqual(e2, 5.0, places=2)
        self.assertAlmostEqual(e3, 0.0, places=2)
        self.assertAlmostEqual(sensor, 1024.0, places=1)
        # Differential EEG: 22.0 - 5.0 = 17.0
        self.assertAlmostEqual(val, 17.0, places=2)
        self.assertTrue(chk)

    def test_parse_sample_prefix_five_channel_with_seq(self):
        """Test SAMPLE prefix with 5 channels: SAMPLE,e1,e2,e3,sensor,seq"""
        line = "SAMPLE,14.5,2.5,0.0,600.0,12345"
        val, e1, e2, e3, sensor, seq, chk = parse_telemetry_packet(line)
        self.assertAlmostEqual(e1, 14.5, places=2)
        self.assertAlmostEqual(e2, 2.5, places=2)
        self.assertAlmostEqual(e3, 0.0, places=2)
        self.assertAlmostEqual(sensor, 600.0, places=1)
        self.assertEqual(seq, 12345)
        self.assertAlmostEqual(val, 12.0, places=2)
        self.assertTrue(chk)

    def test_parse_raw_adc_integers_auto_centering(self):
        """Test raw 12-bit ADC integers (>200) centered around ~2048 counts"""
        # E1 = 2060 counts (~+12 counts = +96.6 uV)
        # E2 = 2040 counts (~-8 counts = -64.4 uV)
        # E3 = 2048 counts (0 uV)
        # Sensor = 1024 counts
        line = "2060, 2040, 2048, 1024"
        val, e1, e2, e3, sensor, seq, chk = parse_telemetry_packet(line)
        self.assertAlmostEqual(sensor, 1024.0, places=1)
        # E1 centered: (2060 - 2048) * 8.05 = 96.6 uV
        self.assertAlmostEqual(e1, 96.6, places=1)
        # E2 centered: (2040 - 2048) * 8.05 = -64.4 uV
        self.assertAlmostEqual(e2, -64.4, places=1)
        # Differential: 96.6 - (-64.4) = 161.0 uV
        self.assertAlmostEqual(val, 161.0, places=1)

    def test_parse_two_channel_eeg_and_sensor(self):
        """Test 2-channel packet: SAMPLE,eeg,sensor"""
        line = "SAMPLE,25.4,350.0"
        val, e1, e2, e3, sensor, seq, chk = parse_telemetry_packet(line)
        self.assertAlmostEqual(val, 25.4, places=2)
        self.assertAlmostEqual(e1, 25.4, places=2)
        self.assertAlmostEqual(e2, 0.0, places=2)
        self.assertAlmostEqual(sensor, 350.0, places=1)

    def test_parse_json_payload(self):
        """Test JSON dictionary payload"""
        payload = json.dumps({
            "e1": 18.2,
            "e2": 3.2,
            "e3": 0.0,
            "sensor": 800.5,
            "seq": 999
        })
        val, e1, e2, e3, sensor, seq, chk = parse_telemetry_packet(payload)
        self.assertAlmostEqual(e1, 18.2, places=2)
        self.assertAlmostEqual(e2, 3.2, places=2)
        self.assertAlmostEqual(e3, 0.0, places=2)
        self.assertAlmostEqual(sensor, 800.5, places=1)
        self.assertEqual(seq, 999)
        self.assertAlmostEqual(val, 15.0, places=2)

    def test_parse_key_value_string(self):
        """Test key-value string: E1:...,E2:...,S:..."""
        line = "E1:12.5, E2:2.5, E3:0.0, S:450"
        val, e1, e2, e3, sensor, seq, chk = parse_telemetry_packet(line)
        self.assertAlmostEqual(e1, 12.5, places=2)
        self.assertAlmostEqual(e2, 2.5, places=2)
        self.assertAlmostEqual(sensor, 450.0, places=1)
        self.assertAlmostEqual(val, 10.0, places=2)

    def test_telemetry_state_multichannel_tracking(self):
        """Test TelemetryState circular buffer and lead tracking"""
        state = TelemetryState()
        self.assertEqual(state.total_packets, 0)
        self.assertEqual(state.latest_leads["e1"], 0.0)
        self.assertEqual(state.latest_leads["sensor"], 0.0)

        # Ingest 3-lead sample
        state.update_sample(
            val=15.0,
            seq=1,
            chk_ok=True,
            sender_ip="192.168.29.100",
            e1=20.0,
            e2=5.0,
            e3=0.0,
            sensor=650.0
        )

        self.assertEqual(state.total_packets, 1)
        self.assertEqual(state.latest_leads["e1"], 20.0)
        self.assertEqual(state.latest_leads["e2"], 5.0)
        self.assertEqual(state.latest_leads["e3"], 0.0)
        self.assertEqual(state.latest_leads["sensor"], 650.0)

        # Check sample_history
        self.assertEqual(len(state.sample_history), 1)
        ts, seq, val, chk_ok, e1, e2, e3, sensor = state.sample_history[0]
        self.assertEqual(val, 15.0)
        self.assertEqual(e1, 20.0)
        self.assertEqual(e2, 5.0)
        self.assertEqual(e3, 0.0)
        self.assertEqual(sensor, 650.0)

        # Check status dictionary
        status = state.get_status_dict()
        self.assertEqual(status["total_packets"], 1)
        self.assertEqual(status["latest_leads"]["e1"], 20.0)
        self.assertEqual(status["latest_leads"]["e2"], 5.0)
        self.assertEqual(status["sensor_value"], 650.0)

        # Check CSV export headers and data
        csv_text = state.get_csv_export()
        self.assertIn("Timestamp_Epoch,Sequence,Microvolts,Checksum_Valid,Electrode_1,Electrode_2,Electrode_3,Sensor_1", csv_text)
        self.assertIn("20.000,5.000,0.000,650.000", csv_text)

        # Check JSON export
        json_data = state.get_json_export()
        self.assertEqual(json_data["latest_leads"]["e1"], 20.0)
        self.assertEqual(json_data["samples"][0]["e1"], 20.0)
        self.assertEqual(json_data["samples"][0]["sensor"], 650.0)

if __name__ == "__main__":
    unittest.main()
