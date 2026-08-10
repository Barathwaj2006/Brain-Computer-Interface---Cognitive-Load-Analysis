# Current Development Status

## Project
NeuroSim × Pokidex 2.0

## Last Agent
Antigravity (Lead Engineer)

## Phase
PHASE 2 — Connection Core Rebuild

## Branch & Baseline
- **Current Branch**: `feature/neurosim-phase-2-connection-core`
- **Baseline Commit**: `78ec98a5e0f083c70c7b5b3322acb198398dbf5`
- **Working Tree**: Clean (`nothing to commit, working tree clean`)

## Core Protocol & Hardware Compliance Flags
- `PROTOCOL_CHANGED=NO`
- `WIFI_ROLE_CHANGED=NO`
- `BLE_ROLE_CHANGED=NO`
- `QR_IMPLEMENTED=NO`
- `PHYSICAL_WIFI_TEST=NOT_TESTED`
- `PHYSICAL_BLE_TEST=NOT_TESTED`

## Tasks Completed (Phase 2)
1. **TASK 1 — Unified Acquisition Contract**: Defined `NormalizedFrame` container in `src/acquisition/contracts.py`.
2. **TASK 2 — Connection Adapter Interface**: Defined `BaseConnectionAdapter` in `src/acquisition/contracts.py` with standard lifecycle methods (`connect`, `disconnect`, `start_stream`, `stop_stream`, `status`, `is_connected`, `is_streaming`, `get_telemetry`).
3. **TASK 3 — Pokidex Wi-Fi Adapter**: `PokidexWifiAdapter` in `src/acquisition/adapters.py` wrapping WebSocket client (`ws://<ip>:8765`).
4. **TASK 4 — Pokidex BLE Adapter**: `PokidexBleAdapter` in `src/acquisition/adapters.py` wrapping BLE GATT peripheral client (`0000fe50`/`0000fe51` with 4-byte chunk reassembly).
5. **TASK 5 — ESP32 USB Adapter**: `ESP32SerialAdapter` in `src/acquisition/adapters.py` with checksum verification.
6. **TASK 6 — ESP32 Wi-Fi Adapter**: `ESP32WifiAdapter` in `src/acquisition/adapters.py` (UDP/TCP streams).
7. **TASK 7 — Simulator Adapter Isolation**: `SimulatorAdapter` in `src/acquisition/adapters.py` explicitly user-activated. Zero automatic fallback.
8. **TASK 8 — Connection State Machine**: Deterministic states (`IDLE`, `SCANNING`, `CONNECTING`, `CONNECTED`, `STREAMING`, `PAUSED`, `DISCONNECTING`, `ERROR`) in `src/app/state.py`.
9. **TASK 9 — Unified Telemetry Model**: `ConnectionTelemetry` dataclass in `src/app/state.py` tracking packets received/dropped, drop %, sequence gaps, latency ms, and errors.
10. **TASK 10 — Hardware Center Refactoring**: `HardwareScreen` in `src/ui/screens/hardware_screen.py` updated to consume real-time `ConnectionTelemetry` without fake values.
11. **TASK 11 — Signal Buffer Integration**: All adapters route validated `NormalizedFrame` payloads to `BoundedSignalBuffer`.
12. **TASK 12 — Disconnection Safety**: Disconnection stops workers, clears telemetry, resets state to `IDLE`, clears buffer, freezes DSP/plots, and performs NO synthetic fallback.
13. **TASK 13 — Automated Tests**: 10 new regression tests in `tests/test_connection_core.py`.
14. **TASK 14 — Manual Validation**: Verified `IDLE` startup, 0 samples, 0 packets, explicit simulator start, and clean disconnect reset.
15. **TASK 15 — Documentation**: Updated `DEVELOPMENT_STATUS.md` and `NEUROSIM_ARCHITECTURE.md`.

## Architecture Summary
- **Acquisition Contracts**: `NormalizedFrame` & `BaseConnectionAdapter` (`src/acquisition/contracts.py`)
- **Transport Adapters**: `PokidexWifiAdapter`, `PokidexBleAdapter`, `ESP32SerialAdapter`, `ESP32WifiAdapter`, `SimulatorAdapter` (`src/acquisition/adapters.py`)
- **State & Telemetry**: `CentralStateManager` & `ConnectionTelemetry` (`src/app/state.py`)
- **UI Integration**: `HardwareScreen.update_telemetry()` (`src/ui/screens/hardware_screen.py`)

## Tests Summary
- **Before Phase 2**: 38/38 PASS
- **After Phase 2**: **48/48 PASS** (`venv\Scripts\python.exe -m pytest`) in 3.80s.

## Known Limitations
- Physical hardware validation over live local Wi-Fi router and real BLE GATT Android peripheral requires physical Android device testing in Phase 13/14 (`PHYSICAL_WIFI_TEST=NOT_TESTED`, `PHYSICAL_BLE_TEST=NOT_TESTED`).

## Files Created
- [`src/acquisition/contracts.py`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/src/acquisition/contracts.py)
- [`src/acquisition/adapters.py`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/src/acquisition/adapters.py)
- [`tests/test_connection_core.py`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/tests/test_connection_core.py)

## Files Modified
- [`src/app/state.py`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/src/app/state.py)
- [`src/acquisition/acquisition_manager.py`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/src/acquisition/acquisition_manager.py)
- [`src/ui/screens/hardware_screen.py`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/src/ui/screens/hardware_screen.py)
- [`src/ui/main_window.py`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/src/ui/main_window.py)
- [`DEVELOPMENT_STATUS.md`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/DEVELOPMENT_STATUS.md)
- [`NEUROSIM_ARCHITECTURE.md`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/NEUROSIM_ARCHITECTURE.md)

## Files Protected (DO NOT MODIFY)
- `src/processing/psd.py` (DSP algorithms & Welch FFT)
- `src/processing/filter.py` (Butterworth filter)
- `src/classification/rule_classifier.py` (Rule-Based Heuristics)
- `src/classification/ml_classifier.py` (Random Forest ML)
- `src/reporting/pdf_generator.py` (ReportLab PDF exporter)
- `firmware/esp32/neurosim_esp32.ino` (ESP32 firmware)

## Recommended Phase 3 Task
**Phase 3: QR Pairing** — Implement zero-configuration QR code generation in NeuroSim Hardware Center displaying local LAN IP endpoint (`ws://<ip>:8765`), BLE GATT parameters, and session nonce for Pokidex scanning.

## Instructions to Google AI Studio
1. Checkout `feature/neurosim-phase-2-connection-core` or pull latest branch before starting.
2. Review [`src/acquisition/contracts.py`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/src/acquisition/contracts.py) and [`src/acquisition/adapters.py`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/src/acquisition/adapters.py).
3. Do not modify protected files or transport adapter UUIDs.
4. Proceed with **Phase 3: QR Pairing**.
