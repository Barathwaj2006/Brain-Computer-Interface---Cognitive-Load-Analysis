"""
Centralized Acquisition Manager for NeuroSim 2.0
Decouples UI screens from low-level transport mechanisms (Serial, Wi-Fi, BLE, Simulator).
Emits normalized sample frames to the application signal buffer and central state manager.
"""

from PySide6.QtCore import QObject, Signal
from src.app.state import CentralStateManager, ConnectionState, InputSource
from src.processing.signal_buffer import BoundedSignalBuffer
from src.acquisition.serial_reader import HardwareSerialThread
from src.acquisition.device_scanner import WifiStreamThread
from src.acquisition.pokidex_client import PokidexDualStreamManager
from src.simulation.eeg_generator import SyntheticEEGGenerator

class AcquisitionManager(QObject):
    """
    Centralized controller for data acquisition.
    Normalizes incoming samples across all transport channels and routes them to the signal buffer.
    """
    normalized_sample_received = Signal(float, dict)

    def __init__(self, state_manager: CentralStateManager, signal_buffer: BoundedSignalBuffer, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self.signal_buffer = signal_buffer

        self.generator = SyntheticEEGGenerator()
        self.hw_serial_thread = None
        self.hw_wifi_thread = None
        self.pokidex_manager = PokidexDualStreamManager()

        # Connect Pokidex dual stream signals
        self.pokidex_manager.sample_received.connect(self._on_pokidex_sample)
        self.pokidex_manager.wifi_connection_changed.connect(self._on_pokidex_connection_changed)
        self.pokidex_manager.ble_connection_changed.connect(self._on_pokidex_connection_changed)

    def start_serial(self, port: str, baudrate: int = 115200):
        """Connects to USB Serial / COM port hardware."""
        self.stop_all()
        self.state_manager.set_source(InputSource.ESP32_USB)
        self.state_manager.transition_to(ConnectionState.CONNECTING, f"● Connecting USB Serial ({port})...")

        self.hw_serial_thread = HardwareSerialThread(target_port=port, baudrate=baudrate)
        self.hw_serial_thread.data_received.connect(self._on_hardware_data)
        self.hw_serial_thread.connection_changed.connect(self._on_hw_connection_changed)
        self.hw_serial_thread.start()

    def start_wifi_stream(self, ip: str, port: int, protocol: str = "UDP"):
        """Connects to ESP32 Wi-Fi UDP/TCP hardware stream."""
        self.stop_all()
        self.state_manager.set_source(InputSource.ESP32_WIFI)
        self.state_manager.transition_to(ConnectionState.CONNECTING, f"● Connecting Wi-Fi Stream ({ip}:{port})...")

        self.hw_wifi_thread = WifiStreamThread(ip=ip, port=port, protocol=protocol)
        self.hw_wifi_thread.data_received.connect(self._on_hardware_data)
        self.hw_wifi_thread.connection_changed.connect(self._on_hw_connection_changed)
        self.hw_wifi_thread.start()

    def start_pokidex_wifi(self, host: str = "127.0.0.1", port: int = 8765):
        """Connects to Pokidex WebSocket server."""
        self.stop_all()
        self.state_manager.set_source(InputSource.POKIDEX_WIFI)
        self.state_manager.transition_to(ConnectionState.CONNECTING, f"● Connecting Pokidex Wi-Fi (ws://{host}:{port})...")
        self.pokidex_manager.start_wifi_stream(host=host, port=port)

    def start_pokidex_ble(self, address: str = None):
        """Connects to Pokidex BLE GATT peripheral."""
        self.stop_all()
        self.state_manager.set_source(InputSource.POKIDEX_BLE)
        self.state_manager.transition_to(ConnectionState.CONNECTING, "● Scanning / Connecting Pokidex BLE...")
        self.pokidex_manager.start_ble_stream(address=address)

    def start_simulator(self):
        """Explicitly starts synthetic simulator mode."""
        self.stop_all()
        self.state_manager.set_source(InputSource.SIMULATOR)
        self.state_manager.transition_to(ConnectionState.STREAMING, "● SIMULATOR ACTIVE (SYNTHETIC MODE)")

    def generate_simulator_chunk(self, num_samples: int = 10):
        """Generates a synthetic chunk if SIMULATOR is active."""
        if self.state_manager.source == InputSource.SIMULATOR and self.state_manager.state == ConnectionState.STREAMING:
            chunk, _ = self.generator.generate_chunk(num_samples=num_samples)
            self.signal_buffer.extend(chunk, source=InputSource.SIMULATOR, metadata={"device": "Synthetic EEG Generator"})
            for s in chunk:
                self.normalized_sample_received.emit(s, {"source": InputSource.SIMULATOR})

    def stop_all(self):
        """Stops all active hardware threads and resets to IDLE zero-input baseline."""
        if self.hw_serial_thread:
            self.hw_serial_thread.stop()
            self.hw_serial_thread = None
        if self.hw_wifi_thread:
            self.hw_wifi_thread.stop()
            self.hw_wifi_thread = None
        if self.pokidex_manager:
            self.pokidex_manager.stop_all()

        self.signal_buffer.clear()
        self.state_manager.reset_to_idle("● DISCONNECTED / IDLE (AWAITING INPUT SOURCE)")

    def _on_hardware_data(self, val: float):
        self.state_manager.transition_to(ConnectionState.STREAMING)
        self.signal_buffer.append(val, source=self.state_manager.source)
        self.normalized_sample_received.emit(val, {"source": self.state_manager.source})

    def _on_pokidex_sample(self, val: float, frame_meta: dict):
        self.state_manager.transition_to(ConnectionState.STREAMING)
        self.signal_buffer.append(val, source=self.state_manager.source, metadata=frame_meta)
        self.normalized_sample_received.emit(val, frame_meta)

    def _on_hw_connection_changed(self, is_connected: bool, status_text: str):
        if is_connected:
            self.state_manager.transition_to(ConnectionState.CONNECTED, status_text)
        else:
            self.state_manager.transition_to(ConnectionState.ERROR, status_text)

    def _on_pokidex_connection_changed(self, is_connected: bool, status_text: str):
        if is_connected:
            self.state_manager.transition_to(ConnectionState.CONNECTED, status_text)
        else:
            self.state_manager.transition_to(ConnectionState.ERROR, status_text)
