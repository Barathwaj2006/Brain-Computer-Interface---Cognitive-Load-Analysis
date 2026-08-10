# Current Development Status

## Project
NeuroSim × Pokidex 2.0

## Last Agent
Antigravity (Lead Engineer)

## Task Completed
NEUROSIM 2.0 — PHASE 0: FORENSIC AUDIT + ARCHITECTURE FREEZE

## Branch & Baseline
- **Current Branch**: `audit/neurosim-phase-0`
- **Baseline Commit**: `0f07bb8b146f17539d1546c1f1a824b876648984`
- **Audit Commit**: `2bb0c6a0aafc9e27dcde3a98da07c99284b7a2a0`
- **Working Tree**: Clean (`nothing to commit, working tree clean`)

## Files Inspected
- `src/main.py`
- `src/ui/main_window.py`
- `src/ui/screens/*.py` (All 15 screen files)
- `src/acquisition/pokidex_client.py`
- `src/acquisition/serial_reader.py`
- `src/acquisition/device_scanner.py`
- `src/processing/psd.py`
- `src/processing/filter.py`
- `src/classification/rule_classifier.py`
- `src/classification/ml_classifier.py`
- `src/reporting/pdf_generator.py`
- `src/simulation/eeg_generator.py`
- `NeuroSim.spec`
- `scripts/build_executable.py`
- `requirements.txt`
- `tests/test_*.py` (All 8 test modules)

## Files Created / Modified
- [`NEUROSIM_AUDIT.md`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/NEUROSIM_AUDIT.md) `[NEW]` Complete Phase 0 Forensic Audit Document.
- [`NEUROSIM_ARCHITECTURE.md`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/NEUROSIM_ARCHITECTURE.md) `[NEW]` 10-Layer Target Architecture & 15-Phase Roadmap.
- [`DEVELOPMENT_STATUS.md`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/DEVELOPMENT_STATUS.md) `[MODIFY]` Agent handoff and status report.

## Summary of Architecture & Subsystems
- **Current UI Architecture**: 15 modular screens managed by `QStackedWidget` inside `MainWindow`.
- **Current Connection Architecture**: Parallel ingestion supporting ESP32 USB Serial (`115200 baud`), ESP32 Wi-Fi UDP/TCP, Pokidex Wi-Fi WebSocket (`ws://0.0.0.0:8765`), and Pokidex BLE GATT (`0000fe50-0000-1000-8000-00805f9b34fb`).
- **Current Protocol**: JSON `SignalFrame` schema (`version`, `source`, `timestamp`, `sequence`, `data`, `metadata`, `events`) and 4-byte header BLE chunk reassembly (`[seq_hi, seq_lo, chunk_idx, total_chunks, JSON...]`).
- **Current Signal Pipeline**: Ingest $\rightarrow$ 1D Ring Buffer (1250 max) $\rightarrow$ Butterworth Bandpass Filter (0.5–50 Hz) $\rightarrow$ Welch PSD (256 NFFT) $\rightarrow$ Dual Classifier (Rule-based $\frac{\theta+\alpha}{\beta}$ + Random Forest ML) $\rightarrow$ ReportLab PDF.
- **Current Build Architecture**: PyInstaller v6.21.0 single executable [`dist/NeuroSim.exe`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/dist/NeuroSim.exe) (**131.27 MB**).

## Test Results
- **Command**: `venv\Scripts\python.exe -m pytest`
- **Result**: **PASS** — 24 passed in 5.99 seconds (0 failures, 2406 joblib NumPy 2.5 warnings).

## Known Issues
- None known.

## Risks & Considerations
- Android OS background power optimization may close Pokidex WebSocket connections during long sessions; auto-reconnect logic must handle session state preservation.
- Local network interfaces may include VirtualBox/Docker bridge IPs; QR pairing generator must select the active default gateway LAN adapter IP.

## Files Currently Protected (DO NOT MODIFY)
- `src/processing/psd.py` (DSP algorithms & Welch FFT)
- `src/processing/filter.py` (Butterworth filter)
- `src/classification/rule_classifier.py` (Rule-Based Heuristics)
- `src/classification/ml_classifier.py` (Random Forest ML)
- `src/reporting/pdf_generator.py` (ReportLab PDF exporter)
- `firmware/esp32/neurosim_esp32.ino` (ESP32 firmware)

## Recommended Phase 1 Task
**Phase 1: NeuroSim Foundation** — Refactor `MainWindow` state management to create a thread-safe `CentralAppState` and decouple the top-level 25 FPS DSP timer into a dedicated worker thread.

## Instructions to Google AI Studio
1. Switch to branch `audit/neurosim-phase-0` or pull latest master before starting.
2. Review [`NEUROSIM_AUDIT.md`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/NEUROSIM_AUDIT.md) and [`NEUROSIM_ARCHITECTURE.md`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/NEUROSIM_ARCHITECTURE.md) to understand the system layout.
3. Do not modify protected files (`src/processing/psd.py`, `src/processing/filter.py`, `src/classification/rule_classifier.py`, `src/classification/ml_classifier.py`, `src/reporting/pdf_generator.py`).
4. Proceed with **Phase 1: NeuroSim Foundation**.
