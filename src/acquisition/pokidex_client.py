"""
Pokidex Dual-Stream Client & Network Acquisition Module
Supports concurrent Wi-Fi (WebSocket JSON SignalFrame server at ws://<ip>:8765)
and Bluetooth Low Energy (BLE GATT Central Client via Bleak) connections to Pokidex Android EEG Stimulator.

Features:
- Parses JSON SignalFrame schema (metadata + data + events)
- Tags incoming samples with source="pokidex" (Wi-Fi) or source="pokidex_ble" (BLE)
- Computes arrival latency (trecv - tsent) and packet loss metrics
- Operates concurrently alongside ESP32 USB/UDP serial checksum reader
"""

import time
import json
import asyncio
from PySide6.QtCore import QThread, QObject, Signal

# Default Pokidex GATT UUID Constants
POKIDEX_SERVICE_UUID = "0000fe50-0000-1000-8000-00805f9b34fb"
POKIDEX_CHAR_DATA_UUID = "0000fe51-0000-1000-8000-00805f9b34fb"
POKIDEX_CHAR_EVENT_UUID = "0000fe52-0000-1000-8000-00805f9b34fb"


class PokidexWebSocketClient(QThread):
    data_received = Signal(float, dict)        # sample_value, frame_meta
    connection_changed = Signal(bool, str)     # is_connected, status_msg
    telemetry_updated = Signal(dict)           # telemetry stats

    def __init__(self, host="127.0.0.1", port=8765):
        super().__init__()
        self.host = host
        self.port = int(port)
        self.running = True
        self.is_connected = False

        self.total_packets = 0
        self.dropped_packets = 0
        self.last_latency_ms = 0.0
        self.last_sequence = -1

    def run(self):
        asyncio.run(self._ws_loop())

    async def _ws_loop(self):
        import websockets

        url = f"ws://{self.host}:{self.port}"
        while self.running:
            try:
                self.connection_changed.emit(False, f"Connecting to Pokidex WebSocket ({url})...")
                async with websockets.connect(url, ping_interval=5.0, timeout=4.0) as ws:
                    self.is_connected = True
                    self.connection_changed.emit(True, f"Pokidex Wi-Fi Connected ({url})")

                    while self.running and self.is_connected:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                            t_recv = time.time()
                            self.parse_signal_frame(msg, t_recv)
                        except asyncio.TimeoutError:
                            continue
                        except Exception as e:
                            self.is_connected = False
                            break

            except Exception as e:
                self.is_connected = False
                self.connection_changed.emit(False, f"Pokidex WebSocket Offline ({url})")
                await asyncio.sleep(2.0)

    def parse_signal_frame(self, raw_msg, t_recv):
        if not raw_msg:
            return

        self.total_packets += 1
        try:
            payload = json.loads(raw_msg)
            t_sent = float(payload.get("timestamp", t_recv))
            self.last_latency_ms = max(0.0, (t_recv - t_sent) * 1000.0)

            seq = payload.get("sequence", 0)
            if self.last_sequence >= 0 and seq > self.last_sequence + 1:
                self.dropped_packets += (seq - self.last_sequence - 1)
            self.last_sequence = seq

            data_arr = payload.get("data", [])
            metadata = payload.get("metadata", {})
            events = payload.get("events", [])

            frame_meta = {
                "source": "pokidex",
                "transport": "Wi-Fi WebSocket",
                "timestamp": t_sent,
                "latency_ms": self.last_latency_ms,
                "sequence": seq,
                "events": events,
                "metadata": metadata
            }

            for sample_val in data_arr:
                val = float(sample_val)
                self.data_received.emit(val, frame_meta)

            pct = (self.dropped_packets / max(1, self.total_packets)) * 100.0
            self.telemetry_updated.emit({
                "source": "pokidex",
                "transport": "Wi-Fi WebSocket",
                "total_packets": self.total_packets,
                "dropped_packets": self.dropped_packets,
                "drop_pct": pct,
                "latency_ms": self.last_latency_ms,
                "events_count": len(events)
            })

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            self.dropped_packets += 1
            pct = (self.dropped_packets / max(1, self.total_packets)) * 100.0
            self.telemetry_updated.emit({
                "source": "pokidex",
                "transport": "Wi-Fi WebSocket",
                "total_packets": self.total_packets,
                "dropped_packets": self.dropped_packets,
                "drop_pct": pct,
                "latency_ms": self.last_latency_ms,
                "events_count": 0
            })

    def stop(self):
        self.running = False
        self.is_connected = False
        self.wait()


class PokidexBleClient(QThread):
    data_received = Signal(float, dict)        # sample_value, frame_meta
    connection_changed = Signal(bool, str)     # is_connected, status_msg
    telemetry_updated = Signal(dict)           # telemetry stats

    def __init__(self, target_address=None, service_uuid=POKIDEX_SERVICE_UUID, char_uuid=POKIDEX_CHAR_DATA_UUID):
        super().__init__()
        self.target_address = target_address
        self.service_uuid = service_uuid
        self.char_uuid = char_uuid
        self.running = True
        self.is_connected = False

        self.total_packets = 0
        self.dropped_packets = 0
        self.last_latency_ms = 0.0
        self.last_sequence = -1
        self.pending_chunks = {}

    def run(self):
        asyncio.run(self._ble_loop())

    async def _ble_loop(self):
        from bleak import BleakClient, BleakScanner

        while self.running:
            try:
                address = self.target_address
                if not address:
                    self.connection_changed.emit(False, "Scanning for Pokidex BLE Peripheral...")
                    devices = await BleakScanner.discover(timeout=3.0)
                    for d in devices:
                        if d.name and "pokidex" in d.name.lower():
                            address = d.address
                            break
                
                if not address:
                    self.connection_changed.emit(False, "Pokidex BLE Peripheral Not Found (Scanning...)")
                    await asyncio.sleep(2.0)
                    continue

                self.connection_changed.emit(False, f"Connecting BLE GATT ({address})...")
                async with BleakClient(address, timeout=5.0) as client:
                    self.is_connected = client.is_connected
                    if self.is_connected:
                        self.connection_changed.emit(True, f"Pokidex BLE GATT Connected ({address})")
                        
                        def notification_handler(sender, data: bytearray):
                            t_recv = time.time()
                            self.parse_ble_frame(data, t_recv)

                        await client.start_notify(self.char_uuid, notification_handler)

                        while self.running and client.is_connected:
                            await asyncio.sleep(0.5)

                        await client.stop_notify(self.char_uuid)

            except Exception as e:
                self.is_connected = False
                self.connection_changed.emit(False, f"Pokidex BLE Offline ({str(e)})")
                await asyncio.sleep(2.0)

    def parse_ble_frame(self, raw_bytes, t_recv):
        if not raw_bytes:
            return

        # Check for 4-byte BLE fragmentation header:
        # byte 0: seq_hi, byte 1: seq_lo, byte 2: chunk_index, byte 3: total_chunks
        if len(raw_bytes) >= 4 and not raw_bytes.startswith(b'{'):
            seq_num = (raw_bytes[0] << 8) | raw_bytes[1]
            chunk_index = raw_bytes[2]
            total_chunks = raw_bytes[3]
            fragment = raw_bytes[4:]

            # Discard any older/incomplete sequences if a new sequence number starts
            stale_seqs = [s for s in self.pending_chunks if s != seq_num]
            for s in stale_seqs:
                del self.pending_chunks[s]
                self.dropped_packets += 1

            if seq_num not in self.pending_chunks:
                self.pending_chunks[seq_num] = {
                    "total": total_chunks,
                    "chunks": {}
                }

            self.pending_chunks[seq_num]["chunks"][chunk_index] = fragment

            # Check if all fragments for seq_num have arrived
            if len(self.pending_chunks[seq_num]["chunks"]) == total_chunks:
                sorted_fragments = [
                    self.pending_chunks[seq_num]["chunks"][i]
                    for i in range(total_chunks)
                    if i in self.pending_chunks[seq_num]["chunks"]
                ]

                if len(sorted_fragments) == total_chunks:
                    full_payload = b"".join(sorted_fragments)
                    del self.pending_chunks[seq_num]
                    self._process_ble_json(full_payload, t_recv)
                else:
                    # Missing chunk index inside sequence
                    del self.pending_chunks[seq_num]
                    self.dropped_packets += 1
        else:
            # Unfragmented bare JSON payload
            self._process_ble_json(raw_bytes, t_recv)

    def _process_ble_json(self, raw_bytes, t_recv):
        self.total_packets += 1
        try:
            msg_text = raw_bytes.decode('utf-8', errors='ignore').strip()
            payload = json.loads(msg_text)
            
            t_sent = float(payload.get("timestamp", t_recv))
            self.last_latency_ms = max(0.0, (t_recv - t_sent) * 1000.0)

            seq = payload.get("sequence", 0)
            if self.last_sequence >= 0 and seq > self.last_sequence + 1:
                self.dropped_packets += (seq - self.last_sequence - 1)
            self.last_sequence = seq

            data_arr = payload.get("data", [])
            metadata = payload.get("metadata", {})
            events = payload.get("events", [])

            frame_meta = {
                "source": "pokidex_ble",
                "transport": "BLE GATT",
                "timestamp": t_sent,
                "latency_ms": self.last_latency_ms,
                "sequence": seq,
                "events": events,
                "metadata": metadata
            }

            for sample_val in data_arr:
                val = float(sample_val)
                self.data_received.emit(val, frame_meta)

            pct = (self.dropped_packets / max(1, self.total_packets)) * 100.0
            self.telemetry_updated.emit({
                "source": "pokidex_ble",
                "transport": "BLE GATT",
                "total_packets": self.total_packets,
                "dropped_packets": self.dropped_packets,
                "drop_pct": pct,
                "latency_ms": self.last_latency_ms,
                "events_count": len(events)
            })

        except (json.JSONDecodeError, ValueError, TypeError):
            self.dropped_packets += 1
            pct = (self.dropped_packets / max(1, self.total_packets)) * 100.0
            self.telemetry_updated.emit({
                "source": "pokidex_ble",
                "transport": "BLE GATT",
                "total_packets": self.total_packets,
                "dropped_packets": self.dropped_packets,
                "drop_pct": pct,
                "latency_ms": self.last_latency_ms,
                "events_count": 0
            })

    def stop(self):
        self.running = False
        self.is_connected = False
        self.wait()


class PokidexDualStreamManager(QObject):
    sample_received = Signal(float, dict)
    wifi_connection_changed = Signal(bool, str)
    ble_connection_changed = Signal(bool, str)
    dual_telemetry_updated = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ws_client = None
        self.ble_client = None
        self.wifi_stats = {}
        self.ble_stats = {}

    def start_wifi_stream(self, host="127.0.0.1", port=8765):
        if self.ws_client:
            self.ws_client.stop()
        self.ws_client = PokidexWebSocketClient(host=host, port=port)
        self.ws_client.data_received.connect(self.sample_received.emit)
        self.ws_client.connection_changed.connect(self.wifi_connection_changed.emit)
        self.ws_client.telemetry_updated.connect(self.on_wifi_telemetry)
        self.ws_client.start()

    def start_ble_stream(self, address=None):
        if self.ble_client:
            self.ble_client.stop()
        self.ble_client = PokidexBleClient(target_address=address)
        self.ble_client.data_received.connect(self.sample_received.emit)
        self.ble_client.connection_changed.connect(self.ble_connection_changed.emit)
        self.ble_client.telemetry_updated.connect(self.on_ble_telemetry)
        self.ble_client.start()

    def on_wifi_telemetry(self, stats):
        self.wifi_stats = stats
        self.emit_dual_telemetry()

    def on_ble_telemetry(self, stats):
        self.ble_stats = stats
        self.emit_dual_telemetry()

    def emit_dual_telemetry(self):
        self.dual_telemetry_updated.emit({
            "wifi": self.wifi_stats,
            "ble": self.ble_stats
        })

    def stop_all(self):
        if self.ws_client:
            self.ws_client.stop()
            self.ws_client = None
        if self.ble_client:
            self.ble_client.stop()
            self.ble_client = None
