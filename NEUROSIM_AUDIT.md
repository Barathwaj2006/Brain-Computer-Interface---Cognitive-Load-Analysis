# NEUROSIM 2.0 — PHASE 0 FORENSIC AUDIT

**Author**: Antigravity (Lead Engineer, NeuroSim 2.0)  
**Branch**: `audit/neurosim-phase-0`  
**Baseline Commit**: `0f07bb8b146f17539d1546c1f1a824b876648984`  
**Date**: August 10, 2026  
**Scope**: Audit Only — Zero Code Modification  

---

## 1. Repository Baseline

- **Repository**: `Brain-Computer-Interface---Cognitive-Load-Analysis`
- **Working Tree**: Clean (`nothing to commit, working tree clean`)
- **Current Branch**: `audit/neurosim-phase-0` (branched from `master` at commit `0f07bb8`)
- **Remotes**:
  - `origin`: `https://github.com/Barathwaj2006/Brain-Computer-Interface---Cognitive-Load-Analysis.git`
- **Environment**: Python 3.14.6 64-bit on Windows 11

---

## 2. Complete Project Inventory

### Root & Configuration Files
- `src/main.py`: Primary application entry point initializing `QApplication` and `MainWindow`.
- `requirements.txt`: Python package requirements (`PySide6`, `pyqtgraph`, `numpy`, `scipy`, `pyserial`, `pandas`, `scikit-learn`, `reportlab`, `pyinstaller`, `matplotlib`, `joblib`, `pytest`, `websockets`, `bleak`).
- `NeuroSim.spec`: PyInstaller executable build specification file.
- `setup.py`: Packaging setup configuration.
- `neurosim_history.db`: SQLite database storing recorded EEG sessions and metrics.

### Module Architecture Map
```text
C:\Users\barat\OneDrive\Documents\neurosim-eeg-cognitive-analysis\
├── android/                         # Android WebView / Java Wrapper (Legacy/Secondary)
│   ├── app/src/main/AndroidManifest.xml
│   └── app/src/main/java/com/neurosim/eeg/MainActivity.java
├── firmware/                        # Hardware Embedded Code
│   └── esp32/neurosim_esp32.ino    # ESP32 C++ firmware (Serial @ 115200 + UDP/TCP)
├── models/                          # Pre-trained Machine Learning Artifacts
│   └── trained_rf_model.joblib      # Random Forest cognitive load classifier model
├── scripts/                         # Build, Training & Maintenance Scripts
│   ├── build_executable.py          # PyInstaller automated build wrapper
│   ├── copy_logo.py                 # Asset copy helper
│   ├── generate_branding_assets.py  # Icon & logo generator
│   └── train_ml_model.py            # Random Forest model trainer
├── src/                             # Core Python Source Code
│   ├── acquisition/                 # Data Ingestion Layer
│   │   ├── base_acquirer.py         # Abstract base acquirer
│   │   ├── device_scanner.py        # COM port & Wi-Fi endpoint scanner
│   │   ├── pokidex_client.py        # Pokidex WS Client, BLE Client & Dual Stream Manager
│   │   └── serial_reader.py         # ESP32 USB Serial Thread & Checksum Validator
│   ├── app/                         # App Configuration
│   │   └── config.py                # Color tokens, constants, sampling defaults
│   ├── classification/              # Cognitive Load Inference Layer
│   │   ├── ai_interpreter.py        # LLM / Rule interpretation engine
│   │   ├── ml_classifier.py         # Random Forest model wrapper
│   │   └── rule_classifier.py       # Deterministic band-power ratio classifier
│   ├── database/                    # Persistence Layer
│   │   └── db_manager.py            # SQLite session manager
│   ├── features/                    # Feature Engineering
│   │   └── extractor.py             # Time & frequency domain feature extractor
│   ├── processing/                  # Signal Processing Layer
│   │   ├── filter.py                # Butterworth bandpass filter
│   │   └── psd.py                   # Welch PSD & band power metrics calculator
│   ├── reporting/                   # Medical Document Exporter
│   │   └── pdf_generator.py         # ReportLab PDF report generator
│   ├── simulation/                  # Synthetic Generator
│   │   └── eeg_generator.py         # SyntheticEEGGenerator (250 Hz multi-band waveform)
│   ├── ui/                          # PySide6 User Interface Layer
│   │   ├── main_window.py           # Main window & top-level DSP dispatch timer (25 FPS)
│   │   ├── components/              # Reusable UI Components (Sidebar, Header, Badges)
│   │   └── screens/                 # 15 Application Screens (Overview, Monitor, Hardware, etc.)
│   └── visualization/               # Custom PyQtGraph & Canvas Widgets
│       ├── animated_brain.py        # 2D/3D Brain visualization widget
│       ├── stress_gauge.py          # Radial cognitive stress meter
│       └── topographic_map.py       # EEG channel spatial heatmap
└── tests/                           # Automated Test Suite (24 Test Cases)
    ├── test_classification.py       # Classifier tests
    ├── test_database.py             # SQLite tests
    ├── test_device_scanner.py       # Scanner tests
    ├── test_idle_behavior.py        # IDLE zero-input state tests
    ├── test_pokidex_client.py       # Pokidex WS & BLE chunk reassembly tests
    ├── test_reporting.py            # PDF generation tests
    ├── test_serial_reader.py        # USB checksum tests
    └── test_signal_processing.py    # DSP & Welch PSD tests
```

---

## 3. Current User Flow

### Step-by-Step Flow:
1. **Launch**: `src/main.py` instantiates `QApplication` and `MainWindow()`.
2. **Initialization**: `MainWindow.__init__()` instantiates DSP tools (`PSDAnalyzer`, `RuleBasedClassifier`, `MLClassifier`), acquirers (`PokidexDualStreamManager`), and sets `self.active_hardware_source = "IDLE"`.
3. **Timer**: `init_dsp_timer()` starts a 25 FPS `QTimer` firing `process_dsp_frame()` every 40 ms.
4. **Acquisition / IDLE Guard**:
   - If `active_hardware_source == "IDLE"` and `len(signal_buffer) < 32`, `process_dsp_frame()` returns immediately without performing computation.
   - If user explicitly selects Simulator Mode (`start_simulator()`), `active_hardware_source` becomes `"SIMULATOR"`, and `SyntheticEEGGenerator.generate_chunk(10)` appends 10 samples every 40 ms.
   - If real hardware or Pokidex streams connect, incoming samples trigger `on_hardware_data()` or `on_pokidex_sample()`, appending to `signal_buffer` and setting state to `"HARDWARE"` or `"POKIDEX"`.
5. **Processing**: When `len(signal_buffer) >= 32`, `psd_analyzer.compute_psd()` executes Welch FFT, computes band powers, and passes features to `RuleBasedClassifier` and `MLClassifier`.
6. **UI Render**: `process_dsp_frame()` updates active UI screen widgets (`screen_overview`, `screen_monitor`, `screen_results`, etc.) at 25 FPS.
7. **Session Recording & Reporting**: Clicking `REC` in `SessionScreen` persists samples to `neurosim_history.db`. Clicking Export PDF calls `pdf_generator.py`.

### Answers to 8 Critical Audit Questions:
1. **Can a waveform appear without a physical device?**  
   *Yes, but ONLY if the user explicitly clicks `🎮 START DEMO SIMULATOR` in Hardware Center.*
2. **Why?**  
   *Because `start_simulator()` explicitly sets `self.active_hardware_source = "SIMULATOR"`, allowing `SyntheticEEGGenerator` to generate synthetic samples.*
3. **Can analysis run without input?**  
   *No. In `IDLE` state (`active_hardware_source == "IDLE"`), `len(signal_buffer)` remains 0 (< 32), causing `process_dsp_frame()` to return early before PSD or classification runs.*
4. **Can reports be generated without real input?**  
   *Only if synthetic simulator mode was activated to populate in-memory metrics; otherwise report metrics remain zero/empty.*
5. **What triggers simulation?**  
   *Explicit click on `🎮 START DEMO SIMULATOR` button in `HardwareScreen` emitting `start_simulator_requested` signal.*
6. **What triggers hardware mode?**  
   *Arrival of valid packet data from USB Serial (`on_hardware_data()`), ESP32 Wi-Fi UDP/TCP, or Pokidex WS/BLE (`on_pokidex_sample()`).*
7. **What happens after disconnect?**  
   *`disconnect_all_hardware()` stops all worker threads, sets `self.active_hardware_source = "IDLE"`, and clears `self.signal_buffer`. All plots freeze.*
8. **What happens after application restart?**  
   *Application boots into `IDLE` state with empty buffer.*

---

## 4. Current Pokidex Connection Flow

### Wi-Fi WebSocket Path
- **Server/Client**: Pokidex Android app acts as WebSocket Server (`ws://0.0.0.0:8765`); NeuroSim acts as Client (`PokidexWebSocketClient` in `src/acquisition/pokidex_client.py`).
- **Initiation**: Triggered by `connect_pokidex_wifi(host, port)`.
- **Handling**: Outer loop retries `websockets.connect()` every 2 seconds if disconnected. Incoming messages parsed via `parse_signal_frame()`.
- **Data Signal**: Emits `data_received(sample_val, frame_meta)` $\rightarrow$ `PokidexDualStreamManager.sample_received` $\rightarrow$ `MainWindow.on_pokidex_sample()`.

### BLE GATT Path
- **Peripheral/Central**: Pokidex Android app acts as BLE GATT Peripheral; NeuroSim acts as BLE Central Client (`PokidexBleClient` in `src/acquisition/pokidex_client.py`).
- **UUIDs**:
  - Service: `0000fe50-0000-1000-8000-00805f9b34fb`
  - Characteristic: `0000fe51-0000-1000-8000-00805f9b34fb` (`NOTIFY` + `READ` only).
- **Reassembly Header**: Each notification has a 4-byte header: `[seq_hi, seq_lo, chunk_idx, total_chunks, JSON_fragment...]`.
- **Handling**: `parse_ble_frame()` buffers fragments in `pending_chunks[seq_num]`. Reassembles and decodes UTF-8 JSON when all `total_chunks` arrive.

---

## 5. QR Pairing Feasibility Audit

### Architectural Analysis:
To enable zero-configuration pairing where NeuroSim displays a QR code and Pokidex scans it:
1. **Local IP Detection**: `socket.gethostbyname_ex(socket.gethostname())` or probing default gateway via socket interface. Must filter out VirtualBox/Docker adapter IPs.
2. **Interface Representation**: Represent active LAN IP (e.g. `192.168.1.100`) and active WebSocket port (`8765` or server port).
3. **BLE Information**: Include local BLE MAC address / Service UUID (`0000fe50`) and device host name.
4. **Security / Session ID**: Include a 16-character cryptographic nonce/session token to authenticate pairing and prevent unauthorized socket connections.

### Recommended QR Payload Schema (JSON):
```json
{
  "protocol": "NEUROSIM_PAIR_v1",
  "session_id": "ns_sess_9a8b7c6d5e4f",
  "timestamp": 1786195000,
  "wifi": {
    "ip": "192.168.1.105",
    "port": 8765,
    "ws_endpoint": "ws://192.168.1.105:8765/pokidex"
  },
  "ble": {
    "service_uuid": "0000fe50-0000-1000-8000-00805f9b34fb",
    "char_uuid": "0000fe51-0000-1000-8000-00805f9b34fb",
    "device_name": "NEUROSIM-STATION"
  }
}
```

---

## 6. Protocol Audit

### SignalFrame Schema Audit:
```text
┌─────────────────┬───────────────────┬────────────────────────────────────────────────────────┐
│ Field           │ Status            │ Description / Code Verification                        │
├─────────────────┼───────────────────┼────────────────────────────────────────────────────────┤
│ version         │ DOCUMENTATION ONLY│ Present in JSON, not validated in parser               │
│ source          │ IMPLEMENTED       │ Tagged as "pokidex" or "pokidex_ble"                   │
│ device ID       │ IMPLEMENTED       │ Extracted from metadata.device                         │
│ timestamp       │ IMPLEMENTED       │ Float timestamp; used for latency calculation          │
│ sequence        │ IMPLEMENTED       │ Int sequence; used for packet loss tracking            │
│ sampling_rate   │ IMPLEMENTED       │ Extracted from metadata.sampling_rate (default 250 Hz) │
│ channel_count   │ DOCUMENTATION ONLY│ Implied by len(data)                                   │
│ channels        │ DOCUMENTATION ONLY│ Not explicitly parsed in current 1D signal_buffer      │
│ data            │ IMPLEMENTED       │ List of float microvolt samples                        │
│ events          │ IMPLEMENTED       │ Extracted list of stimulus event dicts                 │
│ checksum        │ MISSING (JSON)    │ Used in ESP32 CSV path only (SAMPLE,<val>,<seq>,<cs>)  │
│ metadata        │ IMPLEMENTED       │ Dict containing sampling_rate and device metadata      │
│ transport       │ IMPLEMENTED       │ Tagged via source parameter in dual stream manager     │
└─────────────────┴───────────────────┴────────────────────────────────────────────────────────┘
```

---

## 7. Signal Pipeline Audit

### Pipeline Stages & Reliability:
$$\text{Input} \xrightarrow{} \text{Validation (Serial Checksum / JSON Schema)} \xrightarrow{} \text{Signal Buffer (1D List, 1250 Max)}$$
$$\xrightarrow{} \text{Filtering (Butterworth 0.5–50 Hz)} \xrightarrow{} \text{PSD (Welch FFT, 256 NFFT)} \xrightarrow{} \text{Band Powers}$$
$$\xrightarrow{} \text{Metrics } (\alpha/\beta, (\theta+\alpha)/\beta, \text{Stress}) \xrightarrow{} \text{Classifiers (Rule + RF ML)} \xrightarrow{} \text{PDF Report}$$

### Assessment:
- **Sampling Rate**: Hardcoded 250 Hz across filter and Welch NFFT settings. (Production quality for 250 Hz).
- **Buffer Size**: 1250 samples ($5\text{ seconds}$ at $250\text{ Hz}$).
- **PSD Window**: Welch NFFT=256 ($1.024\text{ seconds}$ window, 50% overlap).
- **Band Ranges**:
  - Delta ($\delta$): 0.5–4.0 Hz
  - Theta ($\theta$): 4.0–8.0 Hz
  - Alpha ($\alpha$): 8.0–13.0 Hz
  - Beta ($\beta$): 13.0–30.0 Hz
  - Gamma ($\gamma$): 30.0–45.0 Hz
- **Classifiers**:
  - `RuleBasedClassifier`: Deterministic ratio check $\frac{\theta + \alpha}{\beta}$ (Reliable baseline).
  - `MLClassifier`: Scikit-learn `RandomForestClassifier` trained on 5 band power features (Reliable, model file `models/trained_rf_model.joblib`).

---

## 8. UI/UX Audit

### Existing 15 Screens Evaluation:
1. `OverviewScreen`: **Keep Primary** (Dashboard overview, live metrics, radial gauge).
2. `LiveMonitorScreen`: **Keep Primary** (Real-time multichannel EEG waveform viewer).
3. `HardwareScreen`: **Keep Primary** (Connection Manager, QR code, Device Scanner).
4. `SignalLabScreen`: **Keep Primary** (Analysis tab with filtering & FFT spectrum).
5. `SessionScreen`: **Keep Primary** (Session recording controller & SQLite database list).
6. `ReportScreen`: **Keep Primary** (PDF report exporter & session summary).
7. `SettingsScreen`: **Keep Primary** (App settings, thresholds, port configuration).
8. `ResultsScreen`: **Merge into Analysis** (Displays classification results & margin).
9. `CompareScreen`: **Merge into Analysis** (Comparative session analyzer).
10. `BandAnalysisScreen`: **Merge into Analysis** (Detailed band power breakdown).
11. `ValidationScreen`: **Merge into Settings/Lab** (Hardware & signal quality validation).
12. `ArchitectureScreen`: **Secondary/Documentation** (Block diagram of system).
13. `HistoryScreen`: **Merge into Sessions** (Historical session log).
14. `ExperimentScreen`: **Secondary** (Stimulus protocol controller).
15. `PresentationModeScreen`: **Secondary** (Full-screen kiosk mode).

### Target NeuroSim 2.0 Navigation Alignment:
- **Dashboard**: `OverviewScreen`
- **Connect**: `HardwareScreen` (with QR pairing)
- `Live Monitor`: `LiveMonitorScreen`
- **Analysis**: Consolidated `SignalLabScreen` + `ResultsScreen` + `BandAnalysisScreen`
- **Sessions**: Consolidated `SessionScreen` + `HistoryScreen` + `CompareScreen`
- **Reports**: `ReportScreen`
- **Settings**: `SettingsScreen`

---

## 9. Build Audit

- **Build Configuration**: PyInstaller v6.21.0 using `NeuroSim.spec`.
- **Executable Script**: `scripts/build_executable.py`.
- **Output**: Single standalone executable [`dist/NeuroSim.exe`](file:///C:/Users/barat/OneDrive/Documents/neurosim-eeg-cognitive-analysis/dist/NeuroSim.exe) (**131.27 MB**).
- **Hidden Imports Configured**: `websockets`, `bleak`, `src.acquisition.pokidex_client`, `src.ui.screens.results_screen`, `scipy.signal`, `sklearn.ensemble`.
- **Asset Bundle**: `src/assets/logo.png`, `models/trained_rf_model.joblib` bundled via `datas` in `NeuroSim.spec`.

---

## 10. Test Audit

Executed command:
```powershell
venv\Scripts\python.exe -m pytest
```

### Test Results:
- **Total Tests Collected**: 24
- **Passed**: 24 (100% PASS)
- **Failed**: 0
- **Warnings**: 2,406 (Joblib NumPy 2.5 pickle shape warnings in Python 3.14)
- **Execution Time**: 5.99 seconds

### Test Breakdown by File:
- `tests/test_classification.py`: 3 passed
- `tests/test_database.py`: 2 passed
- `tests/test_device_scanner.py`: 3 passed
- `tests/test_idle_behavior.py`: 3 passed
- `tests/test_pokidex_client.py`: 5 passed
- `tests/test_reporting.py`: 1 passed
- `tests/test_serial_reader.py`: 3 passed
- `tests/test_signal_processing.py`: 4 passed
