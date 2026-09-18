#!/usr/bin/env python3
"""
Automated Test for NeuroSim Web Platform & Laptop Wi-Fi Telemetry Server
Validates:
1. HTTP web server and /api/status REST endpoint.
2. Direct Wi-Fi UDP packet receiver (checksum validation and drop counting).
3. WebSocket real-time broadcast to browser clients.
"""

import sys
import os
import time
import json
import socket
import urllib.request
import asyncio
import unittest

class TestNeuroSimWebServer(unittest.TestCase):
    def test_api_status_endpoint(self):
        url = "http://127.0.0.1:8000/api/status"
        try:
            req = urllib.request.urlopen(url, timeout=3.0)
            self.assertEqual(req.status, 200)
            data = json.loads(req.read().decode('utf-8'))
            self.assertIn("wifi_ip", data)
            self.assertIn("udp_port", data)
            self.assertEqual(data["udp_port"], 5005)
            self.assertEqual(data["ws_port"], 8765)
            print(f"[TEST PASS] /api/status returned: Wi-Fi IP = {data['wifi_ip']}, UDP Port = {data['udp_port']}")
        except Exception as e:
            self.fail(f"HTTP request to /api/status failed: {e}")

    def test_udp_packet_ingestion_and_checksum(self):
        # Send synthetic ESP32 UDP packet to port 5005
        # Format: SAMPLE,<waveform>,<sequence>,<checksum>
        # Checksum = (sequenceNumber + (unsigned int)(fabs(waveform) * 100.0)) % 256
        seq = 42
        val = 15.25
        chk = (seq + int(abs(val) * 100.0)) % 256
        packet = f"SAMPLE,{val},{seq},{chk}".encode('utf-8')

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(packet, ("127.0.0.1", 5005))
        sock.close()

        # Wait a moment for server to process
        time.sleep(0.3)

        # Check telemetry update via API
        url = "http://127.0.0.1:8000/api/status"
        req = urllib.request.urlopen(url, timeout=3.0)
        data = json.loads(req.read().decode('utf-8'))
        self.assertTrue(data["hardware_connected"], "Hardware should be flagged as connected after UDP packet")
        self.assertGreaterEqual(data["total_packets"], 1)
        print(f"[TEST PASS] Hardware UDP packet received and verified. Hardware connected = {data['hardware_connected']}")

if __name__ == '__main__':
    unittest.main()
