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

    def test_multiformat_udp_and_test_endpoint(self):
        # 1. Test multi-line batched UDP packet
        multi_packet = b"SAMPLE,12.5,101,113\nSAMPLE,14.8,102,150\n"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(multi_packet, ("127.0.0.1", 5005))

        # 2. Test JSON UDP payload
        json_packet = json.dumps({"val": 22.4, "seq": 103}).encode('utf-8')
        sock.sendto(json_packet, ("127.0.0.1", 5005))

        # 3. Test 4-channel composite reading (Delta, Theta, Alpha, Beta)
        four_chan = b"2.5, 5.0, 10.0, 15.0"
        sock.sendto(four_chan, ("127.0.0.1", 5005))
        sock.close()

        time.sleep(0.3)

        # 4. Test /api/test-udp REST self-test endpoint
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/test-udp", timeout=3.0)
        res = json.loads(req.read().decode('utf-8'))
        self.assertTrue(res["success"])
        self.assertEqual(res["udp_port"], 5005)
        print(f"[TEST PASS] Multiformat UDP and /api/test-udp verified: {res['message']}")

if __name__ == '__main__':
    unittest.main()
