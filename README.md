# 🧠 NeuroSim — Intelligent EEG Cognitive Analytics & Research Platform

[![Build Windows Executable](https://github.com/Barathwaj2006/Brain-Computer-Interface---Cognitive-Load-Analysis/actions/workflows/build_exe.yml/badge.svg)](https://github.com/Barathwaj2006/Brain-Computer-Interface---Cognitive-Load-Analysis/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20Desktop%20%28x64%29-0078D6.svg)](dist/NeuroSim.exe)
[![Domain](https://img.shields.io/badge/Domain-Neuroscience%20%26%20BCI-purple.svg)]()

**NeuroSim** is a native Windows Desktop Application (`NeuroSim.exe`) designed for real-time Electroencephalography (EEG) signal processing, spectral band power decomposition, 10-20 International System spatial topographic brain mapping, multi-channel oscilloscope trace visualization, automated cognitive load classification, and medical research session reporting.

---

## ✨ Key Features & Medical Visualizations

### 1. 🗺️ **10-20 Topographic Brain Spatial Power Heatmap**
- Real-time 2D spatial power density map across 8 electrode locations (`Fp1`, `Fp2`, `C3`, `C4`, `P3`, `P4`, `O1`, `O2`).
- Smooth color gradient interpolation rendering regional activation (Frontal, Central, Parietal, Occipital).

### 2. 📈 **8-Channel 10-20 System Oscilloscope View**
- Stacked multi-channel trace viewer presenting real-time microvolt (`uV`) voltage swings across all 8 Montage channels.

### 3. 🌊 **Time-Frequency Spectrogram Waterfall Plot**
- Real-time 2D color spectral density heatmap over time (0–40 Hz frequency spectrum).

### 4. 🎛️ **Care-Style Hardware Connection CAD Terminal**
- **Zero-Click Hardware Auto-Lock**: Background USB serial scanner locks onto physical ESP32 acquisition hardware at 115200 baud / 250 Hz instantly.
- **Interactive Digital Potentiometer Control Array**: On-screen control knobs for Delta (2Hz), Theta (6Hz), Alpha (10Hz), and Beta (20Hz) with live voltage (`0.00 V – 3.30 V`) and ADC (`0 – 4095`) readouts.
- **Live Serial Data Packet Monitor**: Terminal monitor streaming raw packet data.

### 5. 📊 **Unified Executive Results & Research Platform**
- Single-view summary combining classified cognitive state (RELAXED, MODERATE, HIGH LOAD), Spectral Stress Index, dominant rhythm, signal quality, spectral band matrix, and one-click PDF report export.

### 6. 🧪 **Automated Validation Center & AI Session Interpreter**
- 10-point mathematical DSP verification suite verifying Welch PSD integration, FFT windowing, band power conservation, and classification determinism.
- AI Session Interpreter providing clinical narrative summaries and feature attributions.

---

## 🏗️ Hardware Wiring & Specifications

NeuroSim interfaces with **ESP32 DevKit V1** hardware configured with 4 potentiometer input channels for synthetic signal modulation:

| Potentiometer | Waveform Frequency | ESP32 Pin | Voltage / ADC |
|---|---|---|---|
| **Pot 1** | **Delta (0.5 – 4 Hz)** | **GPIO 34** (ADC1_CH6) | `0.00V - 3.30V` / `0 - 4095` |
| **Pot 2** | **Theta (4 – 8 Hz)** | **GPIO 35** (ADC1_CH7) | `0.00V - 3.30V` / `0 - 4095` |
| **Pot 3** | **Alpha (8 – 13 Hz)** | **GPIO 32** (ADC1_CH4) | `0.00V - 3.30V` / `0 - 4095` |
| **Pot 4** | **Beta (13 – 30 Hz)** | **GPIO 33** (ADC1_CH5) | `0.00V - 3.30V` / `0 - 4095` |

*Firmware source file available at:* [`firmware/esp32/neurosim_esp32.ino`](firmware/esp32/neurosim_esp32.ino)

---

## 💻 Running NeuroSim

### **Option 1: Launch Pre-Compiled Executable (`NeuroSim.exe`)**
Navigate to the `dist/` directory and double-click:
```text
dist/NeuroSim.exe
```

### **Option 2: Run from Python Source**
1. Clone the repository:
   ```bash
   git clone https://github.com/Barathwaj2006/Brain-Computer-Interface---Cognitive-Load-Analysis.git
   cd Brain-Computer-Interface---Cognitive-Load-Analysis
   ```
2. Create & activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Launch the desktop application:
   ```powershell
   python src/main.py
   ```

---

## 🧪 Automated Testing & System Verification

Run the comprehensive medical diagnostics test suite:
```powershell
python scripts/verify_medical.py
```

---

## 📂 Repository Structure

```text
├── dist/
│   └── NeuroSim.exe               # Standalone Windows Desktop Executable
├── src/
│   ├── acquisition/               # USB Serial Auto-Scanner & Signal Interface
│   ├── app/                       # Config, Tokens, Medical Terminology
│   ├── classification/            # Rule-Based Classifier & AI Interpreter
│   ├── processing/                # Welch PSD Analyzer & Signal Processing
│   ├── reporting/                 # ReportLab Clinical PDF Generator
│   ├── simulation/                # Synthetic EEG Generator Engine
│   ├── ui/                        # PySide6 GUI Screens & Controllers
│   └── visualization/             # Topographic Heatmap, Spectrogram & 8-Ch Montage
├── firmware/
│   └── esp32/                      # ESP32 DevKit Firmware (.ino)
├── scripts/
│   ├── build_executable.py        # PyInstaller Build Automation Script
│   └── verify_medical.py          # System Verification Test Suite
├── NeuroSim.spec                  # PyInstaller Package Configuration
├── requirements.txt               # Python Dependencies
└── README.md                      # Project Documentation
```

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
