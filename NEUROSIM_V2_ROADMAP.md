# NeuroSim 2.0 — Implementation Roadmap & Acceptance Criteria

## Overview
The NeuroSim 2.0 rebuild is structured into 11 execution phases. Each phase is independent, test-driven, and validated before progressing to the next phase.

```
PHASE 0 ──> PHASE 1 ──> PHASE 2 ──> PHASE 3 ──> PHASE 4 ──> PHASE 5
                                                                 │
PHASE 10 <── PHASE 9 <── PHASE 8 <── PHASE 7 <── PHASE 6 <───────┘
```

---

## Phase Breakdown & Acceptance Criteria

### Phase 0: Product & Architecture Specification
- **Status**: COMPLETE
- **Goal**: Establish full product specification, 14-layer architecture blueprint, implementation roadmap, and forensic audit baseline.
- **Tasks**:
  1. Complete repository forensic audit.
  2. Draft `NEUROSIM_V2_PRODUCT_SPEC.md`.
  3. Draft `NEUROSIM_V2_ARCHITECTURE.md`.
  4. Draft `NEUROSIM_V2_ROADMAP.md`.
  5. Update `DEVELOPMENT_STATUS.md`.
- **Acceptance Criteria**: Working tree clean on `rebuild/neurosim-v2`, zero source code modifications, 24/24 baseline unit tests passing.

---

### Phase 1: Core Signal Engine & Contracts
- **Status**: PLANNED
- **Goal**: Refine mathematical synthetic signal generator and canonical `SignalFrame` contract.
- **Tasks**:
  1. Define `SignalFrame` dataclass schema with strict validation rules (sampling rate > 0, sequence >= 0, float data array).
  2. Implement deterministic seeding interface in `SyntheticEEGGenerator`.
  3. Create unit test suite verifying Delta (2Hz), Theta (6Hz), Alpha (10Hz), and Beta (20Hz) peak frequencies.
- **Acceptance Criteria**: 100% test pass on numerical frequency peak validation and frame contract validation.

---

### Phase 2: Signal Acquisition & Thread-Safe Buffer
- **Status**: PLANNED
- **Goal**: Implement `BoundedSignalBuffer`, `SyntheticSignalSource`, and `AcquisitionManager`.
- **Tasks**:
  1. Implement thread-safe `BoundedSignalBuffer` (capacity = 1250 samples @ 250 Hz, FIFO eviction, timestamp & sequence tracking).
  2. Implement generic `BaseSignalSource` abstraction with `start`, `stop`, `pause`, `resume` lifecycle methods.
  3. Implement `SyntheticSignalSource` wrapping `SyntheticEEGGenerator`.
  4. Implement `AcquisitionManager` orchestrating generic signal sources.
  5. Add Phase 2 test suite `tests/test_acquisition_core.py`.
- **Acceptance Criteria**: 18/18 Phase 2 tests passing, 0 buffer overflow beyond 1250 samples, deterministic FIFO eviction.

---

### Phase 3: Quantitative DSP & Feature Extraction
- **Status**: PLANNED
- **Goal**: Implement Welch PSD, Butterworth bandpass filtering, and band power metrics.
- **Tasks**:
  1. Validate Butterworth bandpass filter (0.5 – 30 Hz) and notch filter (50/60 Hz).
  2. Validate Welch PSD computation ($N_{\text{fft}} = 256$, Hanning window, $50\%$ overlap).
  3. Implement `FeatureExtractor` computing Absolute Band Power (ABP), Relative Band Power (RBP), Theta/Beta Ratio (TBR), Alpha/Beta Ratio (ABR), and Engagement Index (EI).
  4. Add DSP numerical validation unit tests.
- **Acceptance Criteria**: Absolute & Relative power integration sums to $100\% \pm 0.1\%$, peak detection within $\pm 0.5\text{ Hz}$ tolerance.

---

### Phase 4: Signal Quality & Cognitive Analysis Engine
- **Status**: PLANNED
- **Goal**: Implement `SignalQualityEvaluator`, `RuleBasedClassifier`, and `MLClassifier`.
- **Tasks**:
  1. Implement real-time `SignalQualityEvaluator` (`NO_SIGNAL`, `INSUFFICIENT_DATA`, `POOR`, `FAIR`, `GOOD`, `EXCELLENT`).
  2. Integrate `RuleBasedClassifier` heuristics.
  3. Integrate `MLClassifier` Random Forest model inference.
  4. Add quality and classification unit tests.
- **Acceptance Criteria**: Correct classification of synthetic baseline vs. cognitive stressor waveforms.

---

### Phase 5: Session Lifecycle & Database Persistence
- **Status**: PLANNED
- **Goal**: Implement `SessionManager` and SQLite storage layer.
- **Tasks**:
  1. Implement `SessionManager` state machine (`IDLE`, `PREPARING`, `RECORDING`, `PAUSED`, `STOPPING`, `COMPLETED`).
  2. Implement SQLite schema (`sessions`, `session_metrics`, `session_events`).
  3. Connect session recording to `BoundedSignalBuffer` snapshots.
  4. Add database persistence unit tests.
- **Acceptance Criteria**: Complete session recording, persistence, and retrieval cycle with 0 data corruption.

---

### Phase 6: Automated PDF Reporting Engine
- **Status**: PLANNED
- **Goal**: Implement ReportLab PDF document generator.
- **Tasks**:
  1. Configure `PDFReportGenerator` layouts and styling.
  2. Generate executive summaries, band ratio charts, and cognitive state analysis tables.
  3. Export PDF documents into `reports/` directory.
  4. Add PDF reporting unit tests.
- **Acceptance Criteria**: Successful generation of valid, uncorrupted PDF documents.

---

### Phase 7: Application UI/UX Rebuild
- **Status**: PLANNED
- **Goal**: Refactor PySide6 desktop interface around `CentralStateManager` and `AcquisitionManager`.
- **Tasks**:
  1. Refactor `MainWindow` to delegate state and buffer management.
  2. Update Live Monitor, Signal Lab, Band Analysis, Session Control, and Reports screens.
  3. Connect UI components to Qt signals emitted by state and acquisition managers.
  4. Perform UI smoke tests.
- **Acceptance Criteria**: Smooth 60 FPS UI rendering, zero UI freezes, zero unhandled Qt exceptions.

---

### Phase 8: Hardware Abstraction & Diagnostics
- **Status**: PLANNED
- **Goal**: Implement transport adapters for ESP32 USB Serial and ESP32 Wi-Fi.
- **Tasks**:
  1. Implement `ESP32SerialAdapter` with sum-mod-256 checksum validation.
  2. Implement `ESP32WifiAdapter` for UDP/TCP data packets.
  3. Refactor Hardware Center UI screen to display real-time connection telemetry.
  4. Add hardware adapter unit tests.
- **Acceptance Criteria**: Hardware adapters conform to `BaseConnectionAdapter` interface; zero synthetic fallback on hardware disconnect.

---

### Phase 9: End-to-End System Validation
- **Status**: PLANNED
- **Goal**: Perform comprehensive end-to-end integration and stability testing.
- **Tasks**:
  1. Execute full regression test suite across all modules.
  2. Perform 1-hour continuous stability run.
  3. Validate PyInstaller executable compilation via `scripts/build_executable.py`.
- **Acceptance Criteria**: 100% test pass, zero memory leaks, successful standalone executable build.

---

### Phase 10: Authorized External-Device Integration
- **Status**: PLANNED (FROZEN / ON HOLD UNTIL AUTHORIZED)
- **Goal**: Integrate authorized external devices (e.g. Pokidex BLE GATT & Wi-Fi WS) when explicitly authorized by project lead.
- **Tasks**:
  1. Implement external device transport adapters.
  2. Verify dual-stream synchronization.
- **Acceptance Criteria**: Clean integration without breaking core NeuroSim architecture.
