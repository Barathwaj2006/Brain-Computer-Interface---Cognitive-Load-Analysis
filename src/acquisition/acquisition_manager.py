"""
Centralized Acquisition Manager for NeuroSim 2.0 (Phase 2 Acquisition Core)
Decouples UI screens and DSP pipeline from specific transport sources.
Manages generic SignalSource instances, routes SignalFrames to SignalBuffer, and tracks acquisition telemetry.
"""

from typing import Optional, Dict
from PySide6.QtCore import QObject, Signal
from src.app.state import CentralStateManager, ConnectionState, InputSource, ConnectionTelemetry
from src.processing.signal_buffer import BoundedSignalBuffer, SignalBuffer
from src.acquisition.contracts import BaseConnectionAdapter, BaseSignalSource, SignalFrame, NormalizedFrame
from src.acquisition.synthetic_source import SyntheticSignalSource
from src.acquisition.pokidex_client import PokidexDualStreamManager
from src.acquisition.adapters import (
    PokidexWifiAdapter,
    PokidexBleAdapter,
    ESP32SerialAdapter,
    ESP32WifiAdapter,
    SimulatorAdapter
)

class AcquisitionManager(QObject):
    """
    Centralized acquisition manager orchestrating generic SignalSource objects and transport adapters.
    Routes SignalFrame / NormalizedFrame objects to BoundedSignalBuffer and updates state_manager.
    """
    normalized_frame_received = Signal(object)  # Emits SignalFrame / NormalizedFrame
    normalized_sample_received = Signal(float, dict) # Backward-compatible sample signal

    def __init__(self, state_manager: CentralStateManager, signal_buffer: BoundedSignalBuffer, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self.signal_buffer = signal_buffer
        self.active_adapter: Optional[BaseConnectionAdapter] = None
        self.active_source: Optional[BaseSignalSource] = None
        
        # Generic SignalSource registry (Task 2.5)
        self._sources: Dict[str, BaseSignalSource] = {}
        
        # Instantiate synthetic source
        self.synthetic_source = SyntheticSignalSource(sampling_rate=signal_buffer.sampling_rate, parent=self)
        self.register_source("synthetic", self.synthetic_source)
        
        # Instantiate available transport adapters
        self.pokidex_wifi_adapter = PokidexWifiAdapter(parent=self)
        self.pokidex_ble_adapter = PokidexBleAdapter(parent=self)
        self.esp32_serial_adapter = ESP32SerialAdapter(parent=self)
        self.esp32_wifi_adapter = ESP32WifiAdapter(parent=self)
        self.simulator_adapter = SimulatorAdapter(parent=self)
        self.pokidex_dual_manager = PokidexDualStreamManager(parent=self)

    @property
    def generator(self):
        return self.simulator_adapter.generator

    @property
    def pokidex_manager(self):
        return self.pokidex_dual_manager

    @property
    def hw_serial_thread(self):
        return self.esp32_serial_adapter._thread

    @property
    def hw_wifi_thread(self):
        return self.esp32_wifi_adapter._thread

    # --- Generic SignalSource Registry Methods (Task 2.5) ---
    def register_source(self, name: str, source: BaseSignalSource):
        """Registers a generic SignalSource instance."""
        self._sources[name] = source

    def select_source(self, name: str) -> bool:
        """Selects and binds an active generic SignalSource by name."""
        if name not in self._sources:
            return False

        self.stop_all()
        self.active_source = self._sources[name]
        self.active_source.frame_received.connect(self._on_normalized_frame)
        return True

    def start(self) -> bool:
        """Starts active generic SignalSource or transport adapter."""
        if self.active_source:
            res = self.active_source.start()
            if res:
                self.state_manager.set_source(InputSource.SIMULATOR)
                self.state_manager.transition_to(ConnectionState.STREAMING, "● SIGNAL SOURCE RUNNING")
            return res
        elif self.active_adapter:
            return self.active_adapter.start_stream()
        return False

    def stop(self) -> bool:
        """Stops active generic SignalSource or transport adapter."""
        return self.stop_all()

    def pause(self) -> bool:
        """Pauses active generic SignalSource."""
        if self.active_source:
            res = self.active_source.pause()
            if res:
                self.state_manager.transition_to(ConnectionState.PAUSED, "● SIGNAL SOURCE PAUSED")
            return res
        return False

    def resume(self) -> bool:
        """Resumes active generic SignalSource from paused state."""
        if self.active_source:
            res = self.active_source.resume()
            if res:
                self.state_manager.transition_to(ConnectionState.STREAMING, "● SIGNAL SOURCE RESUMED")
            return res
        return False

    # --- Legacy Adapter Methods ---
    def _bind_adapter(self, adapter: BaseConnectionAdapter):
        """Binds Qt signals from the active adapter."""
        if self.active_adapter:
            self.active_adapter.disconnect_adapter()
            try:
                self.active_adapter.frame_received.disconnect(self._on_normalized_frame)
                self.active_adapter.telemetry_updated.disconnect(self.state_manager.update_telemetry)
            except RuntimeError:
                pass

        self.active_adapter = adapter
        self.active_adapter.frame_received.connect(self._on_normalized_frame)
        self.active_adapter.telemetry_updated.connect(self.state_manager.update_telemetry)

    def start_serial(self, port: str, baudrate: int = 115200):
        """Connects ESP32 USB Serial stream."""
        self.stop_all()
        self._bind_adapter(self.esp32_serial_adapter)
        self.state_manager.set_source(InputSource.ESP32_USB)
        self.esp32_serial_adapter.connect_adapter(port=port, baudrate=baudrate)

    def start_wifi_stream(self, ip: str, port: int, protocol: str = "UDP"):
        """Connects ESP32 Wi-Fi UDP/TCP stream."""
        self.stop_all()
        self._bind_adapter(self.esp32_wifi_adapter)
        self.state_manager.set_source(InputSource.ESP32_WIFI)
        self.esp32_wifi_adapter.connect_adapter(ip=ip, port=port, protocol=protocol)

    def start_pokidex_wifi(self, host: str = "127.0.0.1", port: int = 8765):
        """Connects Pokidex WebSocket server."""
        self.stop_all()
        self._bind_adapter(self.pokidex_wifi_adapter)
        self.state_manager.set_source(InputSource.POKIDEX_WIFI)
        self.pokidex_wifi_adapter.connect_adapter(host=host, port=port)

    def start_pokidex_ble(self, address: Optional[str] = None):
        """Connects Pokidex BLE GATT peripheral."""
        self.stop_all()
        self._bind_adapter(self.pokidex_ble_adapter)
        self.state_manager.set_source(InputSource.POKIDEX_BLE)
        self.pokidex_ble_adapter.connect_adapter(address=address)

    def start_simulator(self):
        """Explicitly starts synthetic simulator mode (User Action Only)."""
        self.stop_all()
        self.select_source("synthetic")
        self.synthetic_source.start()
        self.state_manager.set_source(InputSource.SIMULATOR)
        self.state_manager.transition_to(ConnectionState.STREAMING, "● SIMULATOR ACTIVE (SYNTHETIC MODE)")

    def generate_simulator_chunk(self, num_samples: int = 10):
        """Generates synthetic chunk ONLY if SIMULATOR is explicitly active."""
        if self.state_manager.source == InputSource.SIMULATOR and self.state_manager.state == ConnectionState.STREAMING:
            frame = self.synthetic_source.generate_frame(num_samples=num_samples)
            self._on_normalized_frame(frame)

    def stop_all(self) -> bool:
        """
        Disconnection Safety:
        Stops all active sources and adapters, clears signal buffer, resets connection state to IDLE.
        NO automatic synthetic fallback.
        """
        if self.active_source:
            self.active_source.stop()
            try:
                self.active_source.frame_received.disconnect(self._on_normalized_frame)
            except RuntimeError:
                pass
            self.active_source = None

        if self.active_adapter:
            self.active_adapter.disconnect_adapter()
            self.active_adapter = None

        self.synthetic_source.stop()
        self.pokidex_wifi_adapter.disconnect_adapter()
        self.pokidex_ble_adapter.disconnect_adapter()
        self.esp32_serial_adapter.disconnect_adapter()
        self.esp32_wifi_adapter.disconnect_adapter()
        self.simulator_adapter.disconnect_adapter()

        self.signal_buffer.clear()
        self.state_manager.reset_to_idle("● DISCONNECTED / IDLE (AWAITING INPUT SOURCE)")
        return True

    def _on_normalized_frame(self, frame: SignalFrame):
        """Ingests a validated SignalFrame into signal_buffer and notifies subscribers."""
        if frame.data is not None and len(frame.data) > 0:
            self.signal_buffer.append_frame(frame)
            for val in frame.data:
                self.normalized_sample_received.emit(float(val), {"source": frame.source, "device": frame.device_id})
        self.normalized_frame_received.emit(frame)
