"""
Unit Tests for Pokidex Dual-Stream Acquisition Subsystem
Tests Wi-Fi WebSocket JSON SignalFrame parsing, BLE GATT notification parsing,
multi-chunk BLE header reassembly, sample tagging with source="pokidex",
latency calculations, and dropped packet tracking.
"""

import time
import json
import unittest
from PySide6.QtWidgets import QApplication
from src.acquisition.pokidex_client import (
    PokidexWebSocketClient, PokidexBleClient, PokidexDualStreamManager,
    POKIDEX_SERVICE_UUID, POKIDEX_CHAR_DATA_UUID
)

app = QApplication.instance() or QApplication([])

class TestPokidexClient(unittest.TestCase):
    def test_gatt_uuids(self):
        self.assertEqual(POKIDEX_SERVICE_UUID, "0000fe50-0000-1000-8000-00805f9b34fb")
        self.assertEqual(POKIDEX_CHAR_DATA_UUID, "0000fe51-0000-1000-8000-00805f9b34fb")

    def test_websocket_signal_frame_parsing(self):
        client = PokidexWebSocketClient()
        received_samples = []
        received_meta = []

        client.data_received.connect(lambda v, m: (received_samples.append(v), received_meta.append(m)))

        t_sent = time.time() - 0.050  # 50 ms latency
        sample_frame = {
            "version": "1.0",
            "source": "pokidex",
            "timestamp": t_sent,
            "sequence": 100,
            "data": [12.5, 15.0, 18.2],
            "metadata": {"sampling_rate": 250, "device": "Pokidex Android"},
            "events": [{"type": "STIMULUS_ON", "label": "ALPHA_10HZ"}]
        }

        t_recv = time.time()
        client.parse_signal_frame(json.dumps(sample_frame), t_recv)

        self.assertEqual(len(received_samples), 3)
        self.assertEqual(received_samples, [12.5, 15.0, 18.2])
        self.assertEqual(received_meta[0]["source"], "pokidex")
        self.assertEqual(received_meta[0]["transport"], "Wi-Fi WebSocket")
        self.assertGreaterEqual(client.last_latency_ms, 40.0)
        self.assertEqual(client.total_packets, 1)
        self.assertEqual(client.dropped_packets, 0)

    def test_ble_signal_frame_parsing(self):
        client = PokidexBleClient()
        received_samples = []
        received_meta = []

        client.data_received.connect(lambda v, m: (received_samples.append(v), received_meta.append(m)))

        t_sent = time.time() - 0.080  # 80 ms latency
        sample_frame = {
            "version": "1.0",
            "source": "pokidex_ble",
            "timestamp": t_sent,
            "sequence": 200,
            "data": [22.1, 24.3],
            "metadata": {"sampling_rate": 250, "device": "Pokidex BLE"},
            "events": []
        }

        t_recv = time.time()
        client.parse_ble_frame(json.dumps(sample_frame).encode('utf-8'), t_recv)

        self.assertEqual(len(received_samples), 2)
        self.assertEqual(received_samples, [22.1, 24.3])
        self.assertEqual(received_meta[0]["source"], "pokidex_ble")
        self.assertEqual(received_meta[0]["transport"], "BLE GATT")
        self.assertGreaterEqual(client.last_latency_ms, 70.0)
        self.assertEqual(client.total_packets, 1)

    def test_ble_fragmented_chunk_reassembly(self):
        client = PokidexBleClient()
        received_samples = []
        received_meta = []

        client.data_received.connect(lambda v, m: (received_samples.append(v), received_meta.append(m)))

        t_sent = time.time() - 0.060
        full_frame = {
            "version": "1.0",
            "source": "pokidex_ble",
            "timestamp": t_sent,
            "sequence": 300,
            "data": [10.1, 11.2, 12.3, 13.4],
            "metadata": {"sampling_rate": 250, "device": "Pokidex GATT Stimulator"},
            "events": [{"type": "STIMULUS_SYNC", "label": "BETA_20HZ"}]
        }

        raw_json_bytes = json.dumps(full_frame).encode('utf-8')
        part_len = len(raw_json_bytes) // 3
        part0 = raw_json_bytes[:part_len]
        part1 = raw_json_bytes[part_len:part_len*2]
        part2 = raw_json_bytes[part_len*2:]

        # 4-byte header: byte0: seq_hi, byte1: seq_lo, byte2: chunk_idx, byte3: total_chunks
        # Sequence number 300 = 0x012C
        hdr0 = bytes([0x01, 0x2C, 0, 3]) + part0
        hdr1 = bytes([0x01, 0x2C, 1, 3]) + part1
        hdr2 = bytes([0x01, 0x2C, 2, 3]) + part2

        t_recv = time.time()
        client.parse_ble_frame(hdr0, t_recv)
        self.assertEqual(len(received_samples), 0)  # Waiting for remaining chunks

        client.parse_ble_frame(hdr1, t_recv)
        self.assertEqual(len(received_samples), 0)  # Waiting for remaining chunks

        client.parse_ble_frame(hdr2, t_recv)
        # All 3 chunks received & reassembled!
        self.assertEqual(len(received_samples), 4)
        self.assertEqual(received_samples, [10.1, 11.2, 12.3, 13.4])
        self.assertEqual(received_meta[0]["source"], "pokidex_ble")
        self.assertEqual(received_meta[0]["sequence"], 300)
        self.assertEqual(received_meta[0]["metadata"]["device"], "Pokidex GATT Stimulator")
        self.assertEqual(len(received_meta[0]["events"]), 1)

    def test_dual_stream_manager(self):
        manager = PokidexDualStreamManager()
        emitted_telemetry = []
        manager.dual_telemetry_updated.connect(emitted_telemetry.append)

        manager.on_wifi_telemetry({"source": "pokidex", "latency_ms": 12.0})
        manager.on_ble_telemetry({"source": "pokidex_ble", "latency_ms": 45.0})

        self.assertEqual(len(emitted_telemetry), 2)
        self.assertEqual(emitted_telemetry[-1]["wifi"]["latency_ms"], 12.0)
        self.assertEqual(emitted_telemetry[-1]["ble"]["latency_ms"], 45.0)

if __name__ == "__main__":
    unittest.main()
