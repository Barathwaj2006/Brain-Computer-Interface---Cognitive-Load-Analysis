# 🧠 NeuroSim — Intelligent EEG Cognitive Analytics & Research Platform

[![Build Windows Executable](https://github.com/Barathwaj2006/Brain-Computer-Interface---Cognitive-Load-Analysis/actions/workflows/build_exe.yml/badge.svg)](https://github.com/Barathwaj2006/Brain-Computer-Interface---Cognitive-Load-Analysis/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20Desktop%20%28x64%29-0078D6.svg)](dist/NeuroSim.exe)
[![Domain](https://img.shields.io/badge/Domain-Neuroscience%20%26%20BCI-purple.svg)]()

**NeuroSim** is a native Windows Desktop Application (`NeuroSim.exe`) designed for real-time Electroencephalography (EEG) signal processing, spectral band power decomposition, 10-20 International System spatial topographic brain mapping, multi-channel oscilloscope trace visualization, dual-model cognitive load classification (Rule-Based & Machine Learning), and research session reporting.

---

## ✨ Key Features & Medical Visualizations

### 1. 🗺️ **10-20 Topographic Brain Spatial Power Heatmap**
- Real-time 2D spatial power density map across 8 electrode locations (`Fp1`, `Fp2`, `C3`, `C4`, `P3`, `P4`, `O1`, `O2`).
- Smooth color gradient interpolation rendering regional activation (Frontal, Central, Parietal, Occipital).

### 2. 📈 **8-Channel 10-20 System Oscilloscope View**
- Stacked multi-channel trace viewer presenting real-time microvolt (`uV`) voltage swings across all 8 Montage channels.

### 3. 🌊 **Time-Frequency Spectrogram Waterfall Plot**
- Real-time 2D color spectral density heatmap over time (0–40 Hz frequency spectrum).

### 4. 🎛️ **Care-Style Hardware Connection CAD Terminal & Checksum Protocol**
- **Zero-Click Hardware Auto-Lock**: Background USB serial scanner locks onto physical ESP32 acquisition hardware at 115200 baud / 250 Hz using `NEUROSIM_HELLO,v1` handshake.
- **Packet Integrity Checksum Protocol**: Validates incoming 4-part packets (`SAMPLE,<val>,<seq>,<checksum>`) and logs dropped packet percentages.
- **Interactive Digital Potentiometer Control Array**: On-screen control knobs for Delta (2Hz), Theta (6Hz), Alpha (10Hz), and Beta (20Hz) with live voltage (`0.00 V – 3.30 V`) and ADC (`0 – 4095`) readouts.

### 5. 📊 **Dual Classifier Panel & Disagreement Warning**
- Displays Rule-Based Heuristic Margin alongside ML Random Forest Statistical Probability side-by-side.
- Automatically flags classifier disagreements with a visual warning banner.

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

## 💻 Running & Building NeuroSim

### **Option 1: Launch Pre-Compiled Executable (`NeuroSim.exe`)**
Navigate to the `dist/` directory and double-click:
```text
dist/NeuroSim.exe
```

### **Option 2: Run from Python Source**
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

### **Option 3: Building Executables with PyInstaller**
- **Single-File Bundle (`NeuroSim.exe`)**:
  ```powershell
  python scripts/build_executable.py
  ```
- **Directory Folder Build (`--onedir`)** (Faster startup & code-signing ready):
  ```powershell
  python scripts/build_executable.py --onedir
  ```

---

## ⚠️ Limitations & Research Scope

1. **Synthetic Simulation**: NeuroSim is a synthetic EEG signal simulator and research demonstration platform; it is **not** a medical device or clinically validated diagnostic tool.
2. **Synthetic-Only Model Evaluation**: The Machine Learning (Random Forest) classifier is trained and evaluated exclusively on synthetic signal profiles. Full clinical validation requires benchmark human EEG datasets (e.g., PhysioNet EEG Motor Movement/Imagery Database).
3. **Heuristic Signal Quality & Contact Checks**: Contact impedance and signal quality metrics represent power-threshold heuristics rather than true clinical hardware impedance measurements.

---

## 🧪 Automated Testing & System Verification

Run unit tests and diagnostic suite:
```powershell
python -m unittest discover tests
python scripts/verify_medical.py
```

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
