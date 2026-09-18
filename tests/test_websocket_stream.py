#!/usr/bin/env python3
"""
Test WebSocket stream relay from UDP to WebSocket client.
"""

import socket
import asyncio
import json
import time
import websockets
import unittest

class TestWebSocketRelay(unittest.TestCase):
    def test_websocket_relay(self):
        async def run_test():
            uri = "ws://127.0.0.1:8765"
            async with websockets.connect(uri) as ws:
                # 1. Receive initial handshake
                handshake_raw = await ws.recv()
                handshake = json.loads(handshake_raw)
                self.assertEqual(handshake.get("app"), "NeuroSim")
                self.assertEqual(handshake.get("udp_port"), 5005)

                # 2. Send UDP packet to 127.0.0.1:5005
                seq = 999
                val = 28.5
                chk = (seq + int(abs(val) * 100.0)) % 256
                packet = f"SAMPLE,{val},{seq},{chk}".encode('utf-8')

                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(packet, ("127.0.0.1", 5005))
                sock.close()

                # 3. Read relayed sample over WebSocket
                received_sample = False
                for _ in range(10):
                    msg_raw = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    msg = json.loads(msg_raw)
                    if msg.get("type") == "batch":
                        samples = msg.get("samples", [])
                        for s in samples:
                            if s.get("seq") == 999:
                                self.assertEqual(s.get("val"), 28.5)
                                self.assertTrue(s.get("chk_ok"))
                                received_sample = True
                                break
                    if received_sample:
                        break

                self.assertTrue(received_sample, "Sample sent via UDP was not received on WebSocket")
                print("[TEST PASS] Live UDP-to-WebSocket bridge confirmed.")

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
