# 🧠 NeuroSim — Intelligent EEG Cognitive Analytics & BCI Research Platform

[![Build Windows Executable](https://img.shields.io/badge/Build-Executable%20Passing-emerald.svg)](dist/NeuroSim.exe)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt-0078D6.svg)](https://www.qt.io/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20Desktop%20%28x64%29-0078D6.svg)](dist/NeuroSim.exe)
[![Domain](https://img.shields.io/badge/Domain-Neuroscience%20%26%20BCI-purple.svg)]()

> **NeuroSim** is a professional desktop application designed for real-time Electroencephalography (EEG) signal processing, spectral band power decomposition, 10-20 International System spatial topographic brain mapping, dual-model cognitive load classification (Rule-Based Heuristics vs Random Forest Machine Learning), real-time Bluetooth/Wi-Fi/USB hardware device acquisition, and automated session report generation.

---

## 📌 Table of Contents

- [Overview & Architecture](#-overview--architecture)
- [Key Features & Capabilities](#-key-features--capabilities)
- [Hardware Connectivity & Device Discovery](#-hardware-connectivity--device-discovery)
- [Repository Structure](#-repository-structure)
- [Installation & Quick Start](#-installation--quick-start)
- [Building Standalone Executable](#-building-standalone-executable)
- [Testing & Verification](#-testing--verification)
- [Research Scope & Disclaimers](#-research-scope--disclaimers)
- [License](#-license)

---

## 🧠 Overview & Architecture

NeuroSim processes continuous time-series EEG waveforms at **250 Hz** through a 5-stage medical-grade digital signal processing (DSP) pipeline:

$$\text{Raw EEG Waveform} \xrightarrow[\text{Bandpass (0.5--40 Hz)}]{\text{Butterworth Filter}} \text{Filtered Signal} \xrightarrow[\text{5-sec Hann Window}]{\text{Welch FFT PSD}} \text{Power Spectrum} \xrightarrow[\Delta, \Theta, \alpha, \beta]{\text{Band Ratios}} \text{Feature Vector} \xrightarrow[\text{Dual Model}]{\text{ML + Rule-Based}} \text{Cognitive Load}$$

### Key DSP Metrics Calculated:
- **Spectral Stress Index (SSI)**: $\frac{\beta}{\alpha + \theta}$
- **Theta / Beta Ratio (TBR)**: $\frac{\theta}{\beta}$ (Attentional engagement metric)
- **Alpha / Beta Ratio (ABR)**: $\frac{\alpha}{\beta}$ (Relaxation vs alertness index)
- **Dominant Peak Frequency**: Peak power frequency ($0 - 40\text{ Hz}$)

---

## ✨ Key Features & Capabilities

### 1. 📊 **Dual Model Cognitive Load Classification**
- **Random Forest ML Classifier**: Trained on spectral band features, predicting statistical confidence percentages ($0-100\%$).
- **Rule-Based Clinical Classifier**: Heuristic threshold evaluator producing explicit `"Rule Margin"` scores.
- **Disagreement Warning Flag**: Automatically highlights classifier conflicts with an alert banner when ML and Rule-Based models predict differing load states (`LOW`, `MODERATE`, `HIGH`).

### 2. 🔬 **5-Stage Signal Laboratory (DSP Pipeline Viewer)**
Interactive inspection workstation allowing researchers to view every stage of signal transformation:
- **Stage 1**: Unfiltered composite waveform ($\mu\text{V}$).
- **Stage 2**: Butterworth bandpass filtered signal ($0.5-40\text{ Hz}$).
- **Stage 3**: Welch Power Spectral Density distribution ($0-40\text{ Hz}$, $\mu\text{V}^2/\text{Hz}$).
- **Stage 4**: Integrated band power bar graph ($\Delta, \Theta, \alpha, \beta$).
- **Stage 5**: Clinical feature vector numerical matrix (TBR, ABR, Stress Index, Latency).

### 3. 🗺️ **10-20 Spatial Topo Map & Oscilloscope Trace**
- **2D Topographic Brain Heatmap**: Real-time spatial power mapping across 8 electrode locations (`Fp1`, `Fp2`, `C3`, `C4`, `P3`, `P4`, `O1`, `O2`).
- **8-Channel Oscilloscope Montage**: Multi-channel voltage trace viewer.
- **Time-Frequency Spectrogram Waterfall**: 2D spectrotemporal heatmap over time.

### 4. 📄 **Automated PDF Report Exporter & AI Narrative**
- One-click ReportLab PDF generation exporting session statistics, spectral band ratios, cognitive state classifications, and AI-generated clinical narrative summaries.

### 5. 📂 **SQLite Session Archive**
- Persistent local SQLite database for session telemetry recording, review, variance delta comparisons (Session A vs Session B), and history management.

---

## 📡 Hardware Connectivity & Device Discovery

NeuroSim features a **Real Hardware Device Discovery & Network Scanner Engine** (`src/acquisition/device_scanner.py`) supporting real hardware without forced dummy connections:

- 🔵 **Bluetooth SPP & USB Serial Scanner**: Discovers active physical serial hardware and Bluetooth Serial Port Profile (SPP) devices on the system.
- 📶 **Wi-Fi Network Stream Receiver (`WifiStreamThread`)**: Receives real-time UDP broadcast streams or TCP socket packets over local Wi-Fi.
- 🛡️ **Packet Integrity Checksum Protocol**: Validates incoming 4-part telemetry packets (`SAMPLE,<value>,<sequence>,<checksum>`) using sum-mod-256 validation and logs packet drop percentages.

### ESP32 DevKit V1 Hardware Pinout

| Hardware Channel | Target Waveform | ESP32 Pin | Analog Range |
|---|---|---|---|
| **Channel 1** | **Delta (0.5 – 4 Hz)** | **GPIO 34** (ADC1_CH6) | `0.00V - 3.30V` / `0 - 4095` |
| **Channel 2** | **Theta (4 – 8 Hz)** | **GPIO 35** (ADC1_CH7) | `0.00V - 3.30V` / `0 - 4095` |
| **Channel 3** | **Alpha (8 – 13 Hz)** | **GPIO 32** (ADC1_CH4) | `0.00V - 3.30V` / `0 - 4095` |
| **Channel 4** | **Beta (13 – 30 Hz)** | **GPIO 33** (ADC1_CH5) | `0.00V - 3.30V` / `0 - 4095` |

*Firmware C++ code available at:* [`firmware/esp32/neurosim_esp32.ino`](firmware/esp32/neurosim_esp32.ino)

---

## 📂 Repository Structure

```text
neurosim-eeg-cognitive-analysis/
├── dist/                        # Compiled standalone executable build (NeuroSim.exe)
├── firmware/
│   └── esp32/
│       └── neurosim_esp32.ino  # ESP32 C++ firmware with checksum protocol
├── models/
│   └── trained_rf_model.joblib # Trained Random Forest ML Classifier
├── reports/                     # Generated PDF session report archive
├── scripts/
│   ├── build_executable.py      # PyInstaller build automation script
│   ├── generate_branding_assets.py # Asset generator script for logos/icons
│   ├── train_ml_model.py       # Random Forest training & OOD evaluation script
│   └── verify_medical.py        # System verification diagnostic runner
├── src/
│   ├── app/
│   │   └── config.py            # Centralized parameters, colors, and branding
│   ├── acquisition/
│   │   ├── device_scanner.py    # Real Bluetooth SPP & Wi-Fi stream scanner
│   │   └── serial_reader.py     # Hardware serial reader thread & checksum validator
│   ├── classification/
│   │   ├── ml_classifier.py     # Random Forest classifier with path resolver
│   │   └── rule_classifier.py   # Clinical rule heuristic classifier
│   ├── database/
│   │   └── db_manager.py        # SQLite database session persistence manager
│   ├── processing/
│   │   ├── filter.py            # Butterworth 0.5-40 Hz bandpass filter
│   │   └── psd.py               # Welch PSD, band extraction, & self-tests
│   ├── reporting/
│   │   ├── ai_engine.py         # Deterministic research narrative generator
│   │   └── pdf_generator.py     # ReportLab PDF session report generator
│   ├── simulation/
│   │   └── eeg_generator.py     # Synthetic EEG signal generator
│   ├── ui/
│   │   ├── components/          # Reusable UI widgets (AppHeader, Sidebar, etc.)
│   │   ├── screens/             # 15 interactive application screen modules
│   │   └── main_window.py       # Main Qt window layout and DSP dispatcher
│   ├── visualization/
│   │   ├── spectrogram_widget.py# 2D Time-Frequency Spectrogram waterfall plot
│   │   ├── spectrogram_view.py  # Compatibility re-export module
│   │   └── styles.py            # Glassmorphism & Qt design stylesheet
│   └── main.py                  # PySide6 application launch entry point
├── tests/                       # Automated unit test suite (16 test cases)
├── NeuroSim.spec                # PyInstaller build specification file
├── README.md                    # Project documentation
└── requirements.txt             # Python dependencies manifest
```

---

## 💻 Installation & Quick Start

### **Option 1: Launch Pre-Compiled Executable (`NeuroSim.exe`)**
Double-click the pre-compiled executable in `dist/`:
```powershell
dist/NeuroSim.exe
```

### **Option 2: Run from Python Source**
1. Clone the repository:
   ```bash
   git clone https://github.com/Barathwaj2006/Brain-Computer-Interface---Cognitive-Load-Analysis.git
   cd Brain-Computer-Interface---Cognitive-Load-Analysis
   ```
2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Launch the application:
   ```powershell
   python src/main.py
   ```

---

## 🛠️ Building Standalone Executable

To compile a standalone Windows executable using PyInstaller:

```powershell
# Standard Single-File Bundle (dist/NeuroSim.exe)
python scripts/build_executable.py

# Fast-Startup Directory Build (--onedir)
python scripts/build_executable.py --onedir
```

---

## 🧪 Testing & Verification

Run the full automated unit test suite and system verification runner:

```powershell
# Run Unit Tests
python -m unittest discover tests

# Run System Verification Suite
python scripts/verify_medical.py
```

---

## ⚠️ Research Scope & Disclaimers

1. **Synthetic Signal Simulation**: NeuroSim is an educational and scientific demonstration platform designed for BCI research. It is **not** a medical device and is not intended for clinical diagnostic use.
2. **Model Evaluation Bounds**: The Machine Learning classifier is evaluated on synthetic EEG profiles. Clinical deployment requires benchmark human dataset validation (e.g. PhysioNet EEG Motor Movement/Imagery Database).
3. **Signal Quality Heuristics**: Contact quality and signal stability indicators represent spectral power heuristics rather than physical electrode-skin impedance measurements.

---

## 📄 License

This project is licensed under the **[MIT License](LICENSE)** — feel free to use, adapt, and build upon it for research and educational purposes.
