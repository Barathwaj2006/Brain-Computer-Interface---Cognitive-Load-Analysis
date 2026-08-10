"""
Unified Transport Adapters for NeuroSim 2.0 (Phase 2 Connection Core)
Encapsulates Pokidex Wi-Fi WS, Pokidex BLE GATT, ESP32 USB Serial, ESP32 Wi-Fi, and Synthetic Simulator
behind the common BaseConnectionAdapter interface.
"""

import time
from typing import Optional, List, Dict
from PySide6.QtCore import Signal
from src.app.state import InputSource, ConnectionState, ConnectionTelemetry
from src.acquisition.contracts import BaseConnectionAdapter, NormalizedFrame
from src.acquisition.pokidex_client import PokidexWebSocketClient, PokidexBleClient
from src.acquisition.serial_reader import HardwareSerialThread
from src.acquisition.device_scanner import WifiStreamThread
from src.simulation.eeg_generator import SyntheticEEGGenerator

class PokidexWifiAdapter(BaseConnectionAdapter):
    """Transport Adapter for Pokidex Android WebSocket Streaming (ws://<ip>:8765)."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8765, parent=None):
        super().__init__(source=InputSource.POKIDEX_WIFI, transport_name="Wi-Fi WebSocket", parent=parent)
        self.host = host
        self.port = port
        self._client: Optional[PokidexWebSocketClient] = None
        self._last_seq = 0
        self._start_time = 0.0

    def connect_adapter(self, host: Optional[str] = None, port: Optional[int] = None) -> bool:
        if host:
            self.host = host
        if port:
            self.port = port

        self.disconnect_adapter()
        self._state = ConnectionState.CONNECTING
        self.connection_state_changed.emit(self._state, f"● Connecting Pokidex Wi-Fi (ws://{self.host}:{self.port})...")

        self._client = PokidexWebSocketClient(host=self.host, port=self.port)
        self._client.data_received.connect(self._on_client_data)
        self._client.connection_changed.connect(self._on_client_connection_changed)
        self._client.telemetry_updated.connect(self._on_client_telemetry)
        self._start_time = time.time()
        self._client.start()
        return True

    def disconnect_adapter(self) -> bool:
        if self._client:
            self._client.stop()
            self._client = None
        self._state = ConnectionState.IDLE
        self._telemetry = ConnectionTelemetry(source=self.source, transport=self.transport_name)
        self.connection_state_changed.emit(self._state, "● DISCONNECTED / IDLE")
        self.telemetry_updated.emit(self._telemetry)
        return True

    def start_stream(self) -> bool:
        if self._client and not self._client.isRunning():
            self._client.start()
        return True

    def stop_stream(self) -> bool:
        return self.disconnect_adapter()

    def _on_client_data(self, val: float, meta: dict):
        if self._state != ConnectionState.STREAMING:
            self._state = ConnectionState.STREAMING
            self.connection_state_changed.emit(self._state, f"● Pokidex Wi-Fi Streaming ({self.host})")

        t_now = time.time()
        seq = meta.get("sequence", self._last_seq + 1)
        if self._last_seq > 0 and seq > self._last_seq + 1:
            gaps = seq - (self._last_seq + 1)
            self._telemetry.sequence_gaps += gaps
            self._telemetry.packets_dropped += gaps
        self._last_seq = seq

        self._telemetry.packets_received += 1
        self._telemetry.last_packet_time = t_now
        self._telemetry.latency_ms = round((t_now - meta.get("timestamp", t_now)) * 1000.0, 2)
        if self._start_time > 0:
            self._telemetry.session_duration = round(t_now - self._start_time, 1)
        self._telemetry.update_drop_percentage()

        frame = NormalizedFrame(
            source=self.source,
            transport=self.transport_name,
            device_id=meta.get("device", f"Pokidex-{self.host}"),
            timestamp=meta.get("timestamp", t_now),
            sequence=seq,
            sampling_rate=meta.get("sampling_rate", 250),
            channel_count=1,
            channels=["Ch1"],
            data=[val],
            events=meta.get("events", []),
            metadata=meta,
            latency_ms=self._telemetry.latency_ms,
            integrity_status="VALID"
        )
        self.frame_received.emit(frame)
        self.telemetry_updated.emit(self._telemetry)

    def _on_client_connection_changed(self, is_connected: bool, msg: str):
        if is_connected:
            self._state = ConnectionState.CONNECTED
        else:
            self._state = ConnectionState.ERROR
            self._telemetry.last_error = msg
            self.error_occurred.emit(msg)
        self.connection_state_changed.emit(self._state, msg)

    def _on_client_telemetry(self, stats: dict):
        self._telemetry.packets_dropped += stats.get("dropped_packets", 0)
        self._telemetry.update_drop_percentage()
        self.telemetry_updated.emit(self._telemetry)


class PokidexBleAdapter(BaseConnectionAdapter):
    """Transport Adapter for Pokidex BLE GATT Notifications."""

    def __init__(self, target_address: Optional[str] = None, parent=None):
        super().__init__(source=InputSource.POKIDEX_BLE, transport_name="BLE GATT", parent=parent)
        self.target_address = target_address
        self._client: Optional[PokidexBleClient] = None
        self._last_seq = 0
        self._start_time = 0.0

    def connect_adapter(self, address: Optional[str] = None, **kwargs) -> bool:
        if address:
            self.target_address = address
        self.disconnect_adapter()
        self._state = ConnectionState.CONNECTING
        self.connection_state_changed.emit(self._state, "● Scanning / Connecting Pokidex BLE GATT...")

        self._client = PokidexBleClient(target_address=self.target_address)
        self._client.data_received.connect(self._on_client_data)
        self._client.connection_changed.connect(self._on_client_connection_changed)
        self._client.telemetry_updated.connect(self._on_client_telemetry)
        self._start_time = time.time()
        self._client.start()
        return True

    def disconnect_adapter(self) -> bool:
        if self._client:
            self._client.stop()
            self._client = None
        self._state = ConnectionState.IDLE
        self._telemetry = ConnectionTelemetry(source=self.source, transport=self.transport_name)
        self.connection_state_changed.emit(self._state, "● DISCONNECTED / IDLE")
        self.telemetry_updated.emit(self._telemetry)
        return True

    def start_stream(self) -> bool:
        if self._client and not self._client.isRunning():
            self._client.start()
        return True

    def stop_stream(self) -> bool:
        return self.disconnect_adapter()

    def _on_client_data(self, val: float, meta: dict):
        if self._state != ConnectionState.STREAMING:
            self._state = ConnectionState.STREAMING
            self.connection_state_changed.emit(self._state, "● Pokidex BLE GATT Streaming")

        t_now = time.time()
        seq = meta.get("sequence", self._last_seq + 1)
        if self._last_seq > 0 and seq > self._last_seq + 1:
            gaps = seq - (self._last_seq + 1)
            self._telemetry.sequence_gaps += gaps
            self._telemetry.packets_dropped += gaps
        self._last_seq = seq

        self._telemetry.packets_received += 1
        self._telemetry.last_packet_time = t_now
        self._telemetry.latency_ms = round((t_now - meta.get("timestamp", t_now)) * 1000.0, 2)
        if self._start_time > 0:
            self._telemetry.session_duration = round(t_now - self._start_time, 1)
        self._telemetry.update_drop_percentage()

        frame = NormalizedFrame(
            source=self.source,
            transport=self.transport_name,
            device_id=meta.get("device", "Pokidex-BLE"),
            timestamp=meta.get("timestamp", t_now),
            sequence=seq,
            sampling_rate=meta.get("sampling_rate", 250),
            channel_count=1,
            channels=["Ch1"],
            data=[val],
            events=meta.get("events", []),
            metadata=meta,
            latency_ms=self._telemetry.latency_ms,
            integrity_status="VALID"
        )
        self.frame_received.emit(frame)
        self.telemetry_updated.emit(self._telemetry)

    def _on_client_connection_changed(self, is_connected: bool, msg: str):
        if is_connected:
            self._state = ConnectionState.CONNECTED
        else:
            self._state = ConnectionState.ERROR
            self._telemetry.last_error = msg
            self.error_occurred.emit(msg)
        self.connection_state_changed.emit(self._state, msg)

    def _on_client_telemetry(self, stats: dict):
        self._telemetry.packets_dropped += stats.get("dropped_packets", 0)
        self._telemetry.update_drop_percentage()
        self.telemetry_updated.emit(self._telemetry)


class ESP32SerialAdapter(BaseConnectionAdapter):
    """Transport Adapter for ESP32 USB Serial Stream (@ 115200 baud)."""

    def __init__(self, port: str = "COM3", baudrate: int = 115200, parent=None):
        super().__init__(source=InputSource.ESP32_USB, transport_name="USB Serial", parent=parent)
        self.port = port
        self.baudrate = baudrate
        self._thread: Optional[HardwareSerialThread] = None

    def connect_adapter(self, port: Optional[str] = None, baudrate: Optional[int] = None) -> bool:
        if port:
            self.port = port
        if baudrate:
            self.baudrate = baudrate
        self.disconnect_adapter()
        self._state = ConnectionState.CONNECTING
        self.connection_state_changed.emit(self._state, f"● Connecting USB Serial ({self.port})...")

        self._thread = HardwareSerialThread(target_port=self.port, baudrate=self.baudrate)
        self._thread.data_received.connect(self._on_data)
        self._thread.connection_changed.connect(self._on_connection_changed)
        self._thread.stats_updated.connect(self._on_stats)
        self._thread.start()
        return True

    def disconnect_adapter(self) -> bool:
        if self._thread:
            self._thread.stop()
            self._thread = None
        self._state = ConnectionState.IDLE
        self._telemetry = ConnectionTelemetry(source=self.source, transport=self.transport_name)
        self.connection_state_changed.emit(self._state, "● DISCONNECTED / IDLE")
        self.telemetry_updated.emit(self._telemetry)
        return True

    def start_stream(self) -> bool:
        if self._thread and not self._thread.isRunning():
            self._thread.start()
        return True

    def stop_stream(self) -> bool:
        return self.disconnect_adapter()

    def _on_data(self, val: float):
        if self._state != ConnectionState.STREAMING:
            self._state = ConnectionState.STREAMING
            self.connection_state_changed.emit(self._state, f"● USB Serial Streaming ({self.port})")

        t_now = time.time()
        self._telemetry.packets_received += 1
        self._telemetry.last_packet_time = t_now
        self._telemetry.update_drop_percentage()

        frame = NormalizedFrame(
            source=self.source,
            transport=self.transport_name,
            device_id=f"ESP32-{self.port}",
            timestamp=t_now,
            sequence=self._telemetry.packets_received,
            sampling_rate=250,
            channel_count=1,
            channels=["Ch1"],
            data=[val],
            integrity_status="VALID"
        )
        self.frame_received.emit(frame)
        self.telemetry_updated.emit(self._telemetry)

    def _on_connection_changed(self, is_connected: bool, msg: str):
        if is_connected:
            self._state = ConnectionState.CONNECTED
        else:
            self._state = ConnectionState.ERROR
            self._telemetry.last_error = msg
            self.error_occurred.emit(msg)
        self.connection_state_changed.emit(self._state, msg)

    def _on_stats(self, stats: dict):
        self._telemetry.packets_dropped += stats.get("dropped_packets", 0)
        self._telemetry.update_drop_percentage()
        self.telemetry_updated.emit(self._telemetry)


class ESP32WifiAdapter(BaseConnectionAdapter):
    """Transport Adapter for ESP32 Wi-Fi Stream (UDP/TCP)."""

    def __init__(self, ip: str = "0.0.0.0", port: int = 8888, protocol: str = "UDP", parent=None):
        super().__init__(source=InputSource.ESP32_WIFI, transport_name="Wi-Fi Stream", parent=parent)
        self.ip = ip
        self.port = port
        self.protocol = protocol
        self._thread: Optional[WifiStreamThread] = None

    def connect_adapter(self, ip: Optional[str] = None, port: Optional[int] = None, protocol: Optional[str] = None) -> bool:
        if ip:
            self.ip = ip
        if port:
            self.port = port
        if protocol:
            self.protocol = protocol
        self.disconnect_adapter()
        self._state = ConnectionState.CONNECTING
        self.connection_state_changed.emit(self._state, f"● Connecting ESP32 Wi-Fi ({self.ip}:{self.port})...")

        self._thread = WifiStreamThread(ip=self.ip, port=self.port, protocol=self.protocol)
        self._thread.data_received.connect(self._on_data)
        self._thread.connection_changed.connect(self._on_connection_changed)
        self._thread.stats_updated.connect(self._on_stats)
        self._thread.start()
        return True

    def disconnect_adapter(self) -> bool:
        if self._thread:
            self._thread.stop()
            self._thread = None
        self._state = ConnectionState.IDLE
        self._telemetry = ConnectionTelemetry(source=self.source, transport=self.transport_name)
        self.connection_state_changed.emit(self._state, "● DISCONNECTED / IDLE")
        self.telemetry_updated.emit(self._telemetry)
        return True

    def start_stream(self) -> bool:
        if self._thread and not self._thread.isRunning():
            self._thread.start()
        return True

    def stop_stream(self) -> bool:
        return self.disconnect_adapter()

    def _on_data(self, val: float):
        if self._state != ConnectionState.STREAMING:
            self._state = ConnectionState.STREAMING
            self.connection_state_changed.emit(self._state, f"● ESP32 Wi-Fi Streaming ({self.ip})")

        t_now = time.time()
        self._telemetry.packets_received += 1
        self._telemetry.last_packet_time = t_now
        self._telemetry.update_drop_percentage()

        frame = NormalizedFrame(
            source=self.source,
            transport=self.transport_name,
            device_id=f"ESP32-WiFi-{self.ip}",
            timestamp=t_now,
            sequence=self._telemetry.packets_received,
            sampling_rate=250,
            channel_count=1,
            channels=["Ch1"],
            data=[val],
            integrity_status="VALID"
        )
        self.frame_received.emit(frame)
        self.telemetry_updated.emit(self._telemetry)

    def _on_connection_changed(self, is_connected: bool, msg: str):
        if is_connected:
            self._state = ConnectionState.CONNECTED
        else:
            self._state = ConnectionState.ERROR
            self._telemetry.last_error = msg
            self.error_occurred.emit(msg)
        self.connection_state_changed.emit(self._state, msg)

    def _on_stats(self, stats: dict):
        self._telemetry.packets_dropped += stats.get("dropped_packets", 0)
        self._telemetry.update_drop_percentage()
        self.telemetry_updated.emit(self._telemetry)


class SimulatorAdapter(BaseConnectionAdapter):
    """Transport Adapter for Synthetic Waveform Generator (Explicit User Action Only)."""

    def __init__(self, parent=None):
        super().__init__(source=InputSource.SIMULATOR, transport_name="Synthetic", parent=parent)
        self.generator = SyntheticEEGGenerator()

    def connect_adapter(self, **kwargs) -> bool:
        self._state = ConnectionState.CONNECTED
        self.connection_state_changed.emit(self._state, "● SIMULATOR READY")
        return True

    def disconnect_adapter(self) -> bool:
        self._state = ConnectionState.IDLE
        self._telemetry = ConnectionTelemetry(source=self.source, transport=self.transport_name)
        self.connection_state_changed.emit(self._state, "● DISCONNECTED / IDLE")
        self.telemetry_updated.emit(self._telemetry)
        return True

    def start_stream(self) -> bool:
        self._state = ConnectionState.STREAMING
        self.connection_state_changed.emit(self._state, "● SIMULATOR ACTIVE (SYNTHETIC MODE)")
        return True

    def stop_stream(self) -> bool:
        return self.disconnect_adapter()

    def generate_chunk(self, num_samples: int = 10) -> List[float]:
        """Generates synthetic chunk when explicitly invoked in STREAMING mode."""
        if self._state != ConnectionState.STREAMING:
            return []

        chunk, _ = self.generator.generate_chunk(num_samples=num_samples)
        t_now = time.time()
        self._telemetry.packets_received += len(chunk)
        self._telemetry.last_packet_time = t_now

        frame = NormalizedFrame(
            source=self.source,
            transport=self.transport_name,
            device_id="Synthetic Generator",
            timestamp=t_now,
            sequence=self._telemetry.packets_received,
            sampling_rate=250,
            channel_count=1,
            channels=["Ch1"],
            data=chunk,
            integrity_status="VALID"
        )
        self.frame_received.emit(frame)
        self.telemetry_updated.emit(self._telemetry)
        return chunk
