# 🧠 NeuroSim — Intelligent EEG Cognitive Analytics & Research Web Platform

[![Web Application](https://img.shields.io/badge/Platform-Web%20Application%20%28HTML5%20%2F%20Canvas%20%2F%20JS%29-0284C7.svg)](http://localhost:8000)
[![Wi-Fi Stream](https://img.shields.io/badge/Hardware-Direct%20Laptop%20Wi--Fi%20%28UDP%205005%29-10B981.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Domain](https://img.shields.io/badge/Domain-Neuroscience%20%26%20BCI-purple.svg)]()

> **NeuroSim** is a real-time web application and neural analytics platform designed for Electroencephalography (EEG) signal processing, Welch Power Spectral Density (PSD) analysis, 10-20 International System spatial topographic brain mapping, dual-model cognitive load classification (Rule-Based Heuristics vs Random Forest Machine Learning), direct laptop Wi-Fi hardware telemetry acquisition, and automated session report generation.

---

## 📌 Table of Contents

- [Overview & Web Architecture](#-overview--web-architecture)
- [Key Features & Capabilities](#-key-features--capabilities)
- [Direct Laptop Wi-Fi Hardware Acquisition](#-direct-laptop-wi-fi-hardware-acquisition)
- [Quick Start](#-quick-start)
- [ESP32 Hardware Pinout & Wi-Fi Firmware](#-esp32-hardware-pinout--wi-fi-firmware)
- [Repository Structure](#-repository-structure)
- [Testing & Verification](#-testing--verification)
- [Research Scope & Disclaimers](#-research-scope--disclaimers)
- [License](#-license)

---

## 🧠 Overview & Web Architecture

NeuroSim runs as a high-performance **Web Application** accessed via your web browser. Incoming analog signals stream directly over your **laptop's Wi-Fi network** into the web dashboard at **250 Hz**, processing through a 5-stage digital signal processing (DSP) pipeline:

$$\text{Raw EEG Waveform} \xrightarrow[\text{Bandpass (0.5--40 Hz)}]{\text{Butterworth Filter}} \text{Filtered Signal} \xrightarrow[\text{5-sec Hann Window}]{\text{Welch FFT PSD}} \text{Power Spectrum} \xrightarrow[\Delta, \Theta, \alpha, \beta]{\text{Band Ratios}} \text{Feature Vector} \xrightarrow[\text{Dual Model}]{\text{ML + Rule-Based}} \text{Cognitive Load}$$

### Key DSP Metrics Calculated:
- **Spectral Stress Index (SSI)**: $\frac{\beta}{\alpha + \theta}$
- **Theta / Beta Ratio (TBR)**: $\frac{\theta}{\beta}$ (Attentional engagement metric)
- **Alpha / Beta Ratio (ABR)**: $\frac{\alpha}{\beta}$ (Relaxation vs alertness index)
- **Dominant Peak Frequency**: Peak power frequency ($0 - 40\text{ Hz}$)

---

## ✨ Key Features & Capabilities

### 1. 📈 **Live Oscilloscope & Welch PSD Workstation**
- **60 FPS Real-Time Canvas**: Continuous scrolling waveform viewer with microvolt grid and ground line.
- **Dynamic Welch PSD Spectrum**: Hann-windowed frequency decomposition ($0 - 40\text{ Hz}$).
- **Spectral Band Decomposition**: Real-time progress bars and percentage distribution across Delta ($0.5-4\text{ Hz}$), Theta ($4-8\text{ Hz}$), Alpha ($8-13\text{ Hz}$), and Beta ($13-30\text{ Hz}$).

### 2. 🔬 **5-Stage Signal Laboratory (DSP Pipeline Viewer)**
Interactive inspection workstation allowing researchers and evaluators to inspect every stage of the DSP pipeline:
- **Stage 1**: Raw composite waveform ($\mu\text{V}$).
- **Stage 2**: Butterworth bandpass filtered signal ($0.5-40\text{ Hz}$, DC offset removed).
- **Stage 3**: Welch Power Spectral Density distribution ($0-40\text{ Hz}$, $\mu\text{V}^2/\text{Hz}$).
- **Stage 4**: Integrated band power bar graph ($\Delta, \Theta, \alpha, \beta$).
- **Stage 5**: Clinical feature vector numerical matrix (TBR, ABR, Stress Index, Latency).

### 3. 🗺️ **10-20 Spatial Topographic Brain Heatmap**
- **2D Topographic Brain Heatmap**: Real-time spatial power mapping across 8 standard electrode locations (`Fp1`, `Fp2`, `C3`, `C4`, `P3`, `P4`, `O1`, `O2`).
- **Electrode Contact Impedance Table**: Contact quality verification (< 5 k$\Omega$ threshold).

### 4. ⚖️ **Dual Model Cognitive Load Classification**
- **Random Forest ML Classifier**: Statistical confidence percentages ($0-100\%$).
- **Rule-Based Clinical Classifier**: Heuristic threshold evaluator producing explicit `"Rule Margin"` scores.
- **Disagreement Warning Banner**: Automatically alerts researchers whenever the ML model and Rule-Based model predict differing cognitive states (`LOW`, `MODERATE`, `HIGH`).

### 5. 📡 **Direct Laptop Wi-Fi Hardware Station**
- Directly receives UDP telemetry packets sent to your laptop's Wi-Fi IP address on port `5005`.
- Displays active laptop Wi-Fi IP, packet counter, drop rate %, live sample rate (Hz), and sender IP.
- Includes a **Demo Simulator** toggle with manual sliders and presets for testing without hardware.

### 6. 📄 **Medical PDF Report Exporter & AI Narrative**
- One-click printable medical report generation exporting session statistics, spectral band ratios, cognitive state classifications, and research interpretation summaries.

### 7. 📁 **Session History Archive**
- Persistent local session recording with duration timer, sample counters, state tags, and search.

---

## 📡 Direct Laptop Wi-Fi Hardware Acquisition

NeuroSim eliminates serial cables by receiving telemetry directly over the **laptop's Wi-Fi interface**:

1. **Connect Hardware**: Connect your ESP32 or Wi-Fi hardware to the same Wi-Fi network as your laptop (or your laptop's Mobile Hotspot).
2. **Target Destination**: Program your ESP32 to send UDP datagrams to:
   - **Target IP**: Your laptop's active Wi-Fi IP (auto-detected and displayed on the web dashboard).
   - **Target Port**: `5005` (UDP).
3. **Packet Protocol**:
   $$\text{SAMPLE},<\text{waveform\_}\mu\text{V}>,<\text{sequence\_number}>,<\text{checksum}>$$
   Where:
   $$\text{checksum} = (\text{sequenceNumber} + \lfloor|\text{waveform}| \times 100\rfloor) \pmod{256}$$

---

## 🚀 Quick Start

Launch the NeuroSim web platform with a single command:

```powershell
python server.py
```

Your default browser will immediately open to:
* **Local Web Dashboard:** [http://localhost:8000](http://localhost:8000)
* **Wi-Fi Network URL:** `http://<your-laptop-wifi-ip>:8000`

---

## 🔌 ESP32 Hardware Pinout & Wi-Fi Firmware

Upload the Wi-Fi telemetry firmware to your ESP32 DevKit V1:
[`firmware/esp32/neurosim_wifi_esp32.ino`](firmware/esp32/neurosim_wifi_esp32.ino)

### ESP32 DevKit V1 Hardware Pinout

| Hardware Channel | Target Waveform | ESP32 Pin | Analog Range |
|---|---|---|---|
| **Channel 1** | **Delta (0.5 – 4 Hz)** | **GPIO 34** (ADC1_CH6) | `0.00V - 3.30V` / `0 - 4095` |
| **Channel 2** | **Theta (4 – 8 Hz)** | **GPIO 35** (ADC1_CH7) | `0.00V - 3.30V` / `0 - 4095` |
| **Channel 3** | **Alpha (8 – 13 Hz)** | **GPIO 32** (ADC1_CH4) | `0.00V - 3.30V` / `0 - 4095` |
| **Channel 4** | **Beta (13 – 30 Hz)** | **GPIO 33** (ADC1_CH5) | `0.00V - 3.30V` / `0 - 4095` |

---

## 📂 Repository Structure

```text
NeuroSim/
├── server.py                   # Master Web Server & Laptop Wi-Fi UDP Gateway
├── serve_local.py              # Convenient launcher proxying to server.py
├── firmware/
│   └── esp32/
│       ├── neurosim_wifi_esp32.ino # ESP32 DevKit V1 Direct Laptop Wi-Fi Firmware
│       └── neurosim_esp32.ino      # Legacy USB Serial Firmware
├── web/                        # Complete Web Application (Website)
│   ├── index.html              # Main HTML5 Single-Page Medical Workstation
│   ├── styles.css              # Clean High-Contrast Dark Slate/Cyan Stylesheet
│   ├── app.js                  # In-Browser Radix-2 FFT DSP, 60 FPS Canvas & Wi-Fi Client
│   ├── pdf_export.js           # Medical Session Report Generator
│   ├── 404.html                # Custom 404 Not Found Page
│   ├── privacy.html            # Clinical Privacy Policy (HIPAA / GDPR Principles)
│   ├── terms.html              # Research Terms of Service & Electrical Isolation Guide
│   ├── favicon.svg             # Vector Waveform Favicon
│   ├── robots.txt              # Search Engine Directives
│   ├── sitemap.xml             # XML Sitemap
│   └── manifest.json           # Web App Manifest
├── server.py                   # Production Wi-Fi UDP Receiver, WebSocket Hub, SQLite DB & Auth Gateway
├── tests/                      # Automated Test Suite (15 Unit & Integration Tests)
│   ├── test_dsp_mathematics.py       # Radix-2 FFT and Shepard IDW Mathematical Verification
│   ├── test_wifi_web_server.py       # Wi-Fi UDP and Web API automated test
│   ├── test_websocket_stream.py      # Live UDP-to-WebSocket relay verification test
│   ├── test_high_throughput_stream.py# 250 Hz UDP streaming packet drop test (0% drop)
│   └── test_production_hardening.py  # SQLite indexes, OTP auth, rate limits, backup/restore
├── README.md                   # Project Documentation
└── requirements.txt            # Python Dependencies
```

---

## 🧪 Testing & Verification

Run the full automated test suite (15 tests covering DSP mathematics, high-throughput UDP streaming, WebSocket relay, rate limiting, and SQLite persistence):

```powershell
python -m unittest tests/test_dsp_mathematics.py tests/test_high_throughput_stream.py tests/test_websocket_stream.py tests/test_wifi_web_server.py tests/test_production_hardening.py
```

---

## ⚠️ Research Scope & Disclaimers

1. **Synthetic Signal Simulation**: NeuroSim is an educational and scientific demonstration platform designed for BCI research and simulation. It is not a certified medical device and is not intended for clinical diagnostic use.
2. **Signal Quality Heuristics**: Contact quality and signal stability indicators represent spectral power heuristics rather than physical electrode-skin impedance measurements.

---

## 📄 License

This project is licensed under the **[MIT License](LICENSE)**.
