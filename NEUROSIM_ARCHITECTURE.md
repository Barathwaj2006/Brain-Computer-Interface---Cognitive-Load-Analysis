# NEUROSIM 2.0 — TARGET ARCHITECTURE & ROADMAP

**Author**: Antigravity (Lead Engineer, NeuroSim 2.0)  
**Branch**: `audit/neurosim-phase-0`  
**Date**: August 10, 2026  

---

## 1. Conceptual 10-Layer System Architecture

NeuroSim 2.0 enforces strict decoupled unidirectional data flow across 10 architectural layers:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        1. User Interface Layer                         │
│   Dashboard • Connect • Live Monitor • Analysis • Sessions • Reports   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (PySide6 Signals / Qt Slots)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   2. Application State Manager Layer                   │
│      Centralized AppState (Source Mode, Recording, Selected Channel)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      3. Connection Manager Layer                       │
│    Orchestrates USB Serial, Wi-Fi WebSocket, and BLE GATT Connections │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           4. Transport Layer                           │
│  pyserial (COM)  │  websockets (TCP 8765)  │  bleak (GATT 0000fe50)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Raw Frames / JSON Fragments)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      5. Protocol Validation Layer                      │
│      Checksum Verification • 4-Byte BLE Header • SignalFrame Schema    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Valid Microvolt Floating Samples)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      6. Signal Acquisition Layer                       │
│       Standardized BaseAcquirer Interface (`data_received` signal)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         7. Signal Buffer Layer                         │
│            Ring-Buffer Thread-Safe Queue (1250 Max Capacity)           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      8. Signal Processing Layer                        │
│          Butterworth Bandpass Filter (0.5–50 Hz) • Welch PSD           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Frequency Band Power Spectrum)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           9. Analysis Layer                            │
│  Rule-Based Classifier Ratio  │  Random Forest ML  │  LLM Interpreter  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Cognitive Load State & Margin)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           10. Reporting Layer                          │
│     ReportLab PDF Engine  │  SQLite Recording Database Persistence     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer Responsibilities & Module Allocation

| Layer | Responsibility | Existing Preserved Modules | Future Refactored / New Modules |
| :--- | :--- | :--- | :--- |
| **1. UI Layer** | Renders graphs, controls, status indicators | `OverviewScreen`, `LiveMonitorScreen` | Consolidated 7-Screen Layout |
| **2. App State** | Maintains global application state | `MainWindow` properties | `CentralAppState` controller |
| **3. Connection Mgr** | Handles hardware discovery & state | `PokidexDualStreamManager` | `ConnectionManager` |
| **4. Transport** | Low-level IO (Sockets, Serial, Bluetooth) | `pyserial`, `websockets`, `bleak` | `TransportAdapter` interface |
| **5. Protocol Val** | Validates packets, reassembles chunks | `parse_ble_frame()` | `SignalFrameValidator` |
| **6. Acquisition** | Normalizes sample streams | `base_acquirer.py` | Unified `StreamReceiver` |
| **7. Signal Buffer** | Thread-safe ring buffer for DSP | `signal_buffer` (1250 samples) | `LockFreeRingBuffer` |
| **8. Processing** | Filtering & Welch PSD computation | `filter.py`, `psd.py` | `DSPPipeline` |
| **9. Analysis** | Dual classification & metrics | `rule_classifier.py`, `ml_classifier.py` | `AnalysisEngine` |
| **10. Reporting** | Exports PDF medical documents & DB | `pdf_generator.py`, `db_manager.py` | `ReportGenerator` |

---

## 3. Preserved vs Refactored Modules

### Preserved Modules (Zero Modification Required):
- `src/processing/filter.py`: High-quality Butterworth bandpass filter.
- `src/processing/psd.py`: Accurate Welch PSD and frequency band extractor.
- `src/classification/rule_classifier.py`: Deterministic band power cognitive ratio classifier.
- `src/classification/ml_classifier.py`: Random Forest ML classifier loading `models/trained_rf_model.joblib`.
- `src/reporting/pdf_generator.py`: Medical PDF report generator.
- `firmware/esp32/neurosim_esp32.ino`: Production ESP32 firmware.

### Modules to Refactor / Reorganize:
- `src/ui/main_window.py`: Decouple top-level dispatch timer into dedicated `DSPWorker` thread.
- `src/ui/screens/`: Streamline 15 screens into 7 clean primary tabs.
- `src/acquisition/device_scanner.py`: Add QR code generation & local IP adapter binding.

---

## 4. Phase Breakdown Validation (Phases 0 – 14)

```text
PHASE 0: Audit & Architecture Freeze (COMPLETED)
   │
   ▼
PHASE 1: NeuroSim Foundation (Decoupled Thread-Safe AppState & RingBuffer)
   │
   ▼
PHASE 2: Connection Core (Unified Transport & Network IP Adapter Manager)
   │
   ▼
PHASE 3: QR Pairing (QR Code Generator in Hardware Center & Payload Schema)
   │
   ▼
PHASE 4: Signal Pipeline (Validated Multi-Channel Stream Pipeline)
   │
   ▼
PHASE 5: Scientific Analysis (Band Power & Cognitive Metrics Optimization)
   │
   ▼
PHASE 6: Analysis + AI (LLM Interpreter & Advanced Dual Classifier)
   │
   ▼
PHASE 7: Sessions + Reports (SQLite Persistence & Enhanced Medical PDF Exports)
   │
   ▼
PHASE 8: UI/UX (Consolidated 7-Tab Navigation: Dashboard, Connect, Monitor, Analysis, Sessions, Reports, Settings)
   │
   ▼
PHASE 9: Hardening (PyInstaller Onefile Executable Optimization & Windows Testing)
   │
   ▼
PHASE 10: Pokidex Foundation (Pokidex Android App Protocol & GATT Service Sync)
   │
   ▼
PHASE 11: Pokidex Connectivity (Pokidex QR Scanner & Dual WS/BLE Client Integration)
   │
   ▼
PHASE 12: Pokidex Stimulator/UI (Android EEG Stimulator UI & Event Frame Dispatcher)
   │
   ▼
PHASE 13: System Integration (End-to-End Pokidex-to-NeuroSim Stream Benchmarking)
   │
   ▼
PHASE 14: Physical Validation & Release Build (Physical Hardware Testing & v2.0 Release)
```

### Dependency Validation Note:
All phase dependencies are strictly monotonic and sequential. Phase 0 audit confirms that Phases 1–9 focus on desktop NeuroSim stabilization before Phase 10–13 Pokidex mobile app coupling.
