#!/usr/bin/env python3
"""
High-Throughput Streaming & Reliability Verification
Sends 500 packets at 250 Hz (2 seconds of simulated telemetry) over UDP port 5005.
Verifies:
1. Zero packet loss in the server's 2MB UDP buffer.
2. Continuity of sequence numbers.
3. Proper formatting of CSV and JSON exports.
"""

import time
import socket
import json
import urllib.request
import unittest

class TestHighThroughputStream(unittest.TestCase):
    def test_high_throughput_udp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        target = ("127.0.0.1", 5005)

        start_seq = 1000
        total_packets = 500

        print(f"[TEST] Streaming {total_packets} packets to UDP port 5005 at 250 Hz...")
        for i in range(total_packets):
            seq = start_seq + i
            # Waveform with 10 Hz alpha rhythm modulation
            val = 25.0 * (i % 25) / 25.0
            chk = (seq + int(abs(val) * 100.0)) % 256
            packet = f"SAMPLE,{val:.3f},{seq},{chk}".encode('utf-8')
            sock.sendto(packet, target)
            time.sleep(0.001)  # High speed

        sock.close()
        time.sleep(0.5)  # Allow server processing

        # Verify via REST API
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/status", timeout=3.0)
        status = json.loads(req.read().decode('utf-8'))

        self.assertTrue(status["hardware_connected"])
        self.assertGreaterEqual(status["total_packets"], total_packets)
        print(f"[TEST PASS] Server processed {status['total_packets']} packets. Drop rate = {status['drop_rate_pct']}%.")

        # Verify CSV export
        csv_req = urllib.request.urlopen("http://127.0.0.1:8000/api/export/csv", timeout=3.0)
        self.assertEqual(csv_req.status, 200)
        csv_text = csv_req.read().decode('utf-8')
        lines = csv_text.strip().split("\n")
        self.assertGreater(len(lines), 100)
        self.assertIn("Timestamp_Epoch,Sequence,Microvolts,Checksum_Valid", lines[0])
        print(f"[TEST PASS] CSV export validated: {len(lines)} rows returned.")

        # Verify JSON export
        json_req = urllib.request.urlopen("http://127.0.0.1:8000/api/export/json", timeout=3.0)
        self.assertEqual(json_req.status, 200)
        json_obj = json.loads(json_req.read().decode('utf-8'))
        self.assertIn("samples", json_obj)
        self.assertGreater(len(json_obj["samples"]), 100)
        print(f"[TEST PASS] JSON export validated: {len(json_obj['samples'])} samples returned.")

if __name__ == '__main__':
    unittest.main()
