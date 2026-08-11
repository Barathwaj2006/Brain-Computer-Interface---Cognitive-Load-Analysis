# 🧠 NeuroSim 3.0 — Intelligent EEG Cognitive Analytics & BCI Research Platform

[![Version](https://img.shields.io/badge/Release-v3.0.0--RC-emerald.svg)](DEVELOPMENT_STATUS.md)
[![Test Suite](https://img.shields.io/badge/Pytest-91%2F91%20PASS-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Authoritative%20Runtime%20%2B%20Web%20UI-purple.svg)]()

> **NeuroSim 3.0** is an integrated, scientific-grade application for real-time Electroencephalography (EEG) signal acquisition, spectral band power decomposition, cognitive load workload classification, multi-session longitudinal research analytics, BIDS 1.8.0 dataset exporting, and real-time neurofeedback protocols.

---

## 📌 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Complete Feature List](#-complete-feature-list)
- [Scientific Metrics & Formulas](#-scientific-metrics--formulas)
- [Installation & Setup](#-installation--setup)
- [Running the Application](#-running-the-application)
- [Simulator Workflow](#-simulator-workflow)
- [Research Platform, BIDS & Export Capabilities](#-research-platform-bids--export-capabilities)
- [Real-Time Neurofeedback Protocols](#-real-time-neurofeedback-protocols)
- [Verification & Test Evidence](#-verification--test-evidence)
- [Limitations & Safety Disclaimer](#-limitations--safety-disclaimer)

---

## 🧠 Architecture Overview

NeuroSim 3.0 employs a strict, decoupled single-authoritative-runtime architecture:

```text
Synthetic Signal Generator / Simulator
         │
         ▼
 AcquisitionManager (Frame Ingestion & Telemetry)
         │
         ▼
 BoundedSignalBuffer (1250-sample Rolling Window @ 250 Hz)
         │
         ▼
 PSDAnalyzer (Welch FFT & Morlet Wavelet Decomposition)
         │
         ▼
 EEGFeatureExtractor (Delta, Theta, Alpha, Beta Ratios)
         │
         ▼
 RuleBasedClassifier (Cognitive Workload State: LOW / MODERATE / HIGH)
         │
         ▼
 DatabaseManager (SQLite Persistence: neurosim_history.db)
         │
         ▼
 RuntimeService & HTTP Server (serve_local.py @ localhost:8000)
         │
         ▼
 Modern Glassmorphism Web Interface (web/app.js & web/index.html)
```

- **Authoritative Server Runtime**: All EEG signal generation, rolling buffer storage, Welch PSD spectral calculations, and rule-based classifications occur strictly on the Python backend (`RuntimeController`).
- **Thin Web Frontend**: The browser renders server-provided waveforms, PSD spectrums, and metrics. It performs zero client-side EEG generation or mathematical approximations.

---

## ✨ Complete Feature List

1. 📊 **Executive Dashboard & Live Monitor**
   - Real-time 4-channel EEG signal streaming (`FP1`, `FP2`, `O1`, `O2`).
   - Selectable time-window views (1-second, 2-second, 5-second).
   - Real-time Welch Power Spectral Density (PSD) plot ($0 – 40\text{ Hz}$).
   - Live cognitive workload state (`LOW`, `MODERATE`, `HIGH`) and confidence score.

2. 🔬 **Quantitative Band Analysis**
   - Relative spectral power decomposition: Delta ($0.5–4\text{ Hz}$), Theta ($4–8\text{ Hz}$), Alpha ($8–13\text{ Hz}$), Beta ($13–30\text{ Hz}$).
   - Clinical ratio metrics: Theta/Beta Ratio (TBR), Alpha/Beta Ratio (ABR), Engagement Index, and Total Power ($\mu\text{V}^2/\text{Hz}$).

3. 📂 **Historical Session Archive & Detail Inspector**
   - Automatic SQLite persistence upon session completion.
   - Interactive Session Detail Inspector rendering exact spectral band distributions for past recordings.
   - One-click PDF clinical report downloader.
   - Safe session deletion with instant UI grid refresh.

4. 🧪 **Research Platform & Longitudinal Analytics**
   - Longitudinal progression tracker graphing stress index trends across sessions.
   - Side-by-side session comparison matrix (Session A vs Session B).
   - BIDS (Brain Imaging Data Structure) v1.8.0 metadata exporter (`bids_dataset_description.json`).
   - Full research dataset CSV exporter (`neurosim_research_dataset.csv`) for R, Python, and MATLAB data science pipelines.

5. 🎯 **Real-Time Neurofeedback Protocol Engine**
   - Live Alpha Enhancement protocol ($8–13\text{ Hz}$ target $\ge 30\%$).
   - Attention Focus Index ($TBR \le 2.5$).
   - Beta Boosting protocol for active alertness.

6. ⚙️ **System Configuration & Logging**
   - Dedicated Settings view exposing sampling rate, montage channels, window size, and medical filters (Notch 50/60Hz, EOG, EMG).
   - Rotating file logging (`logs/neurosim_runtime.log`).

---

## 📐 Scientific Metrics & Formulas

NeuroSim 3.0 computes standard quantitative EEG (qEEG) metrics:

- **Relative Band Power**:
  $$P_{\text{rel}}(\text{band}) = \frac{\int_{f_{\text{low}}}^{f_{\text{high}}} \text{PSD}(f) \, df}{\int_{0.5}^{40} \text{PSD}(f) \, df} \times 100\%$$

- **Spectral Stress Index**:
  $$\text{Stress Index} = \frac{P_{\beta}}{P_{\alpha} + P_{\theta}}$$

- **Theta / Beta Ratio (TBR)**:
  $$\text{TBR} = \frac{P_{\theta}}{P_{\beta}}$$

- **Alpha / Beta Ratio (ABR)**:
  $$\text{ABR} = \frac{P_{\alpha}}{P_{\beta}}$$

- **Engagement Index**:
  $$\text{Engagement} = \frac{P_{\beta}}{P_{\alpha} + P_{\theta}}$$

---

## 📥 Installation & Setup

### Prerequisites
- Python 3.11, 3.12, or 3.14 (x64)
- Git

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/Barathwaj2006/Brain-Computer-Interface---Cognitive-Load-Analysis.git
cd Brain-Computer-Interface---Cognitive-Load-Analysis

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install production dependencies
pip install -r requirements.txt
```

---

## 🚀 Running the Application

### Option A: Local Browser Application (Recommended)

```bash
python serve_local.py
```

This starts the NeuroSim HTTP API server on `http://127.0.0.1:8000` and automatically opens the web dashboard in your default browser.

### Option B: PySide6 Native Desktop GUI

```bash
python src/main.py
```

---

## 🔄 Simulator Workflow

1. Launch `python serve_local.py`.
2. Click **START SESSION** in the Executive Dashboard or Session Control.
3. The synthetic signal generator streams real-time 4-channel EEG waveforms with adjustable cognitive workload states.
4. Click **PAUSE** to halt streaming without losing accumulated duration.
5. Click **RESUME** to continue data ingestion.
6. Click **STOP** to finalize the session and persist it to `neurosim_history.db`.
7. Navigate to **History Archive** or **Reports Platform** to export PDF reports or compare sessions.

---

## 📊 Research Platform, BIDS & Export Capabilities

- **CSV Export**: Click `EXPORT RESEARCH DATASET (CSV)` to download `neurosim_research_dataset.csv` containing session IDs, timestamps, band powers, stress indices, and classification states.
- **BIDS Export**: Click `EXPORT BIDS JSON` to generate Brain Imaging Data Structure v1.8.0 metadata (`bids_dataset_description.json`).
- **PDF Reports**: Export formal clinical reports using ReportLab with spectral plots, band breakdowns, and interpretive diagnostic summaries.

---

## 🎯 Real-Time Neurofeedback Protocols

1. Navigate to the **Neurofeedback** tab in the web interface.
2. Select target protocol:
   - **Alpha Enhancement**: Target $\ge 30\%$ relative Alpha power for relaxation training.
   - **Theta/Beta Reduction**: Target $TBR \le 2.5$ for attentional focus training.
   - **Beta Boosting**: Focus score tracking for active alertness.
3. The interface displays real-time `OPTIMAL TARGET`, `STABLE REGULATION`, or `SUB-THRESHOLD` feedback states.

---

## 🧪 Verification & Test Evidence

NeuroSim 3.0 includes a comprehensive test suite covering all modules:

```bash
venv\Scripts\python.exe -m pytest
```

### Verified Test Results: **91 / 91 PASSED** (100% Clean Execution)

| Test Module | Tests | Status |
|---|:---:|:---:|
| `tests/test_acquisition_core.py` | 16 | **PASS** |
| `tests/test_api_bridge.py` | 3 | **PASS** |
| `tests/test_api_server.py` | 8 | **PASS** |
| `tests/test_classification.py` | 3 | **PASS** |
| `tests/test_database.py` | 2 | **PASS** |
| `tests/test_device_scanner.py` | 3 | **PASS** |
| `tests/test_e2e_master_lifecycle.py` | 1 | **PASS** |
| `tests/test_idle_behavior.py` | 3 | **PASS** |
| `tests/test_pipeline_integration.py` | 8 | **PASS** |
| `tests/test_pokidex_client.py` | 5 | **PASS** |
| `tests/test_reporting.py` | 1 | **PASS** |
| `tests/test_research_platform.py` | 4 | **PASS** |
| `tests/test_runtime.py` | 17 | **PASS** |
| `tests/test_serial_reader.py` | 3 | **PASS** |
| `tests/test_signal_contract.py` | 10 | **PASS** |
| `tests/test_signal_processing.py` | 4 | **PASS** |
| **Total** | **91** | **PASS (100%)** |

---

## ⚠️ Limitations & Safety Disclaimer

> **RESEARCH & EDUCATIONAL USE ONLY**: NeuroSim 3.0 is a software simulation and research visualization platform. It is **not** a certified medical device and is **not** intended for clinical diagnosis, treatment planning, or patient monitoring. Simulator sessions consume synthetic waveforms and are explicitly identified as simulated data. Physical hardware connectivity (ESP32/BLE) is disconnected per project architectural boundaries.

---

## 📜 License

Distributed under the [MIT License](LICENSE).
