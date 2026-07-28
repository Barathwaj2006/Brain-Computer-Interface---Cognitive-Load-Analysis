# NEUROSIM — Synthetic EEG Cognitive Analysis & Clinical Stress Platform

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-Qt6-green?logo=qt)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Windows-blue?logo=windows)

> A professional biomedical desktop application for real-time synthetic EEG signal generation, spectral band analysis (Delta/Theta/Alpha/Beta), cognitive load classification, clinical stress metrics, and PDF report generation.

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Architecture](#architecture)
- [Hardware](#hardware)
- [Circuit Connections](#circuit-connections)
- [Software Installation](#software-installation)
- [Running the Application](#running-the-application)
- [Simulation Mode](#simulation-mode)
- [Hardware Mode](#hardware-mode)
- [Signal Processing Pipeline](#signal-processing-pipeline)
- [Classification System](#classification-system)
- [Machine Learning Model](#machine-learning-model)
- [Report Generation](#report-generation)
- [Building NeuroSim.exe](#building-neurosimexe)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Limitations](#limitations)
- [Future Work](#future-work)

---

## Overview

**NeuroSim** is a standalone Windows desktop application built with Python + PySide6 (Qt6) that simulates a complete EEG cognitive analysis pipeline:

```
EEG Signal → Signal Processing → FFT/PSD → Band Power Analysis → Feature Extraction → Classification → Live Visualization → PDF Report
```

The application provides:
- **Real-time scrolling EEG waveform** with high-FPS PyQtGraph rendering
- **Welch PSD frequency spectrum** (0–40 Hz) with band region highlighting
- **Delta/Theta/Alpha/Beta band power** bars and percentages
- **Spectral Stress Index**, Cognitive Fatigue (TBR), and Engagement metrics
- **Rule-Based & Machine Learning** cognitive load classifiers
- **Clinical Biofeedback Breathing Assistant** (4-7-8 guided breathing)
- **Custom animated QPainter widgets** (neural brain canvas, stress gauge)
- **SQLite session database** for recording and reviewing sessions
- **Professional PDF report generation** with ReportLab
- **ESP32 hardware serial communication** for potentiometer-controlled waveforms

---

## Problem Statement

**Original Concept:** Build a system that reads human brain EEG signals via electrodes, processes them through an acquisition circuit, performs frequency-band analysis, and generates cognitive assessments.

**Prototype Reality:** Reliable human EEG acquisition hardware is unavailable for this college prototype. Therefore, only the acquisition stage is replaced with a **synthetic EEG generator** — either software-based (Simulation Mode) or hardware-based (ESP32 with potentiometers).

All signal processing, spectral analysis, feature extraction, and classification are performed identically to how they would operate with real EEG data.

> ⚠️ **DISCLAIMER:** This prototype analyses synthetic EEG-like signals for demonstration and development purposes. The results are NOT a medical diagnosis or validated assessment of a person's neurological or psychological condition.

---

## Architecture

```
                                +---------------------------+
                                |  ESP32 Hardware (4 Pots)  |
                                +-------------+-------------+
                                              | USB Serial (250Hz)
                                              v
+------------------------+      +---------------------------+
|  Synthetic Simulator   | ---> |  Data Acquisition Engine  |
| (Interactive Sliders)  |      +-------------+-------------+
+------------------------+                    | Ring Buffer (2500 samples)
                                              v
                                +---------------------------+
                                | Signal Processing Engine  |
                                | (Detrend, Bandpass, PSD)  |
                                +-------------+-------------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
                     v                                                 v
        +--------------------------+                      +--------------------------+
        | Band Power Analysis      |                      | Clinical Stress Metrics  |
        | (Delta, Theta, Alpha,    |                      | (Stress Index, Fatigue,  |
        |  Beta, Dominant Freq)    |                      |  Engagement, Relaxation) |
        +------------+-------------+                      +------------+-------------+
                     |                                                 |
                     +------------------------+------------------------+
                                              |
                                              v
                                +---------------------------+
                                | Classifier (Rule / ML RF) |
                                +-------------+-------------+
                                              |
                                              v
                                +---------------------------+
                                | PySide6 GUI Dashboard     |
                                | (Live Waveform, Stress    |
                                |  Gauges, Biofeedback)     |
                                +-------------+-------------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
                     v                                                 v
        +--------------------------+                      +--------------------------+
        | SQLite Session Storage   |                      | ReportLab PDF Generator  |
        +--------------------------+                      +--------------------------+
```

---

## Hardware

### Components

| Component | Quantity | Purpose |
|---|---|---|
| ESP32 DevKit V1 | 1 | Synthetic signal generator |
| 10kΩ Potentiometers | 4 | Delta / Theta / Alpha / Beta amplitude control |
| Push buttons | Optional | Session control |
| LED indicators | Optional | Status feedback |
| Breadboard + Jumper wires | 1 set | Prototyping |
| USB cable (Micro-USB) | 1 | ESP32 to laptop serial |

---

## Circuit Connections

```
ESP32 DevKit V1 Pinout:

Potentiometer 1 (Delta Control):
  Outer pins → 3.3V and GND
  Wiper → GPIO 34 (ADC1_CH6)

Potentiometer 2 (Theta Control):
  Outer pins → 3.3V and GND
  Wiper → GPIO 35 (ADC1_CH7)

Potentiometer 3 (Alpha Control):
  Outer pins → 3.3V and GND
  Wiper → GPIO 32 (ADC1_CH4)

Potentiometer 4 (Beta Control):
  Outer pins → 3.3V and GND
  Wiper → GPIO 33 (ADC1_CH5)
```

### ESP32 Firmware Setup

1. Open `firmware/esp32/neurosim_esp32.ino` in Arduino IDE.
2. Install the ESP32 board package in Arduino IDE.
3. Select **ESP32 Dev Module** as the target board.
4. Upload the firmware.
5. The ESP32 will output serial data at **115200 baud** in format: `SAMPLE,<value>`

---

## Software Installation

### Prerequisites
- Python 3.10+ (tested with Python 3.14)
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/neurosim-eeg-cognitive-analysis.git
cd neurosim-eeg-cognitive-analysis

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Running the Application

### From Source

```bash
# Activate virtual environment
venv\Scripts\activate

# Launch the application
python src/main.py
```

### From Packaged Executable

Simply double-click `dist/NeuroSim.exe` — no Python installation required.

---

## Simulation Mode

The application works **completely without hardware** in Simulation Mode:

1. Launch NeuroSim
2. Click **ENTER PLATFORM** on the splash screen
3. Default mode is **SIMULATION MODE**
4. Navigate to **Live Monitor** to see the live waveform
5. Go to **Settings** to adjust Delta/Theta/Alpha/Beta slider amplitudes and noise level
6. Watch the waveform, PSD spectrum, band powers, and cognitive classification update in real-time

---

## Hardware Mode

When an ESP32 is connected:

1. Go to **Settings** → configure COM port (or leave on AUTO)
2. On the **Home Dashboard**, click **HARDWARE MODE (ESP32)**
3. The application will auto-detect the ESP32 serial device
4. Potentiometer adjustments will change the synthetic waveform in real-time

The application handles disconnections gracefully and will **never crash** on hardware failure.

---

## Signal Processing Pipeline

```
RAW SIGNAL → Buffer → Detrend/DC Removal → Butterworth Bandpass (0.5-40 Hz)
→ Welch PSD (5-sec window) → Band Power Integration → Feature Extraction
```

### EEG Frequency Bands

| Band | Frequency Range | Clinical Association |
|---|---|---|
| Delta (δ) | 0.5 – 4.0 Hz | Deep sleep, slow-wave activity |
| Theta (θ) | 4.0 – 8.0 Hz | Drowsiness, meditation, memory |
| Alpha (α) | 8.0 – 13.0 Hz | Relaxed alertness, calm focus |
| Beta (β) | 13.0 – 30.0 Hz | Active concentration, stress |

### Clinical Stress Metrics

- **Spectral Stress Index (SSI):** β / (α + θ)
- **Cognitive Fatigue (TBR):** θ / β
- **Engagement Index:** β / (α + θ)
- **Alpha/Beta Ratio:** Relaxation vs. Focus

---

## Classification System

### Rule-Based Classifier (Default)

| Cognitive Load | Decision Boundary |
|---|---|
| **HIGH** | Beta ≥ 35% OR Stress Index ≥ 0.8 |
| **MODERATE** | Alpha ≥ 35% OR (Alpha ≥ 30% AND Beta < 30%) |
| **LOW** | All other patterns (Delta/Theta dominant) |

### Machine Learning Classifier (Optional)

- **Algorithm:** Random Forest (100 trees, max depth 10)
- **Training Data:** 1500 synthetic EEG samples (6 spectral profiles × 250 samples each)
- **Features:** 8 spectral features (relative band powers, TBR, ABR, Stress Index, log total power)
- **Accuracy:** 100% on test set (synthetic data model)

To retrain the model:

```bash
python scripts/train_ml_model.py
```

---

## Report Generation

After stopping a session, generate a professional PDF report containing:

- Session metadata (ID, timestamp, duration, sampling rate)
- EEG band power breakdown table with clinical interpretations
- Relative band distribution bar chart
- Cognitive load & stress diagnostics
- Mandatory biomedical disclaimer

Reports are saved in the `reports/` directory.

---

## Building NeuroSim.exe

```bash
# Activate virtual environment
venv\Scripts\activate

# Build with PyInstaller
python scripts/build_executable.py

# OR directly:
pyinstaller --noconfirm NeuroSim.spec
```

The executable will be created at `dist/NeuroSim.exe`.

---

## Testing

```bash
# Run all unit tests
python -m pytest tests/ -v

# Individual test modules
python -m pytest tests/test_signal_processing.py -v
python -m pytest tests/test_classification.py -v
python -m pytest tests/test_database.py -v
python -m pytest tests/test_reporting.py -v
```

### Test Coverage

| Test | Validates |
|---|---|
| `test_delta_dominance` | 2 Hz signal → Delta band dominant |
| `test_theta_dominance` | 6 Hz signal → Theta band dominant |
| `test_alpha_dominance` | 10 Hz signal → Alpha band dominant |
| `test_beta_dominance` | 20 Hz signal → Beta band dominant |
| `test_rule_high_beta` | High Beta → HIGH cognitive load |
| `test_rule_alpha_moderate` | High Alpha → MODERATE load |
| `test_ml_predict` | ML classifier returns valid prediction |
| `test_save_and_retrieve_session` | SQLite save & fetch |
| `test_delete_session` | SQLite delete |
| `test_pdf_generation` | PDF file creation & size |

---

## Project Structure

```
neurosim-eeg-cognitive-analysis/
├── README.md
├── requirements.txt
├── setup.py
├── NeuroSim.spec
├── firmware/
│   └── esp32/
│       └── neurosim_esp32.ino
├── src/
│   ├── main.py
│   ├── app/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── acquisition/
│   │   ├── serial_reader.py
│   │   └── base_acquirer.py
│   ├── simulation/
│   │   └── eeg_generator.py
│   ├── processing/
│   │   ├── filter.py
│   │   └── psd.py
│   ├── features/
│   │   └── extractor.py
│   ├── classification/
│   │   ├── rule_classifier.py
│   │   └── ml_classifier.py
│   ├── database/
│   │   └── db_manager.py
│   ├── reporting/
│   │   └── pdf_generator.py
│   ├── visualization/
│   │   ├── custom_widgets.py
│   │   ├── animated_brain.py
│   │   ├── stress_gauge.py
│   │   ├── biofeedback_widget.py
│   │   └── styles.py
│   └── ui/
│       ├── main_window.py
│       └── screens/
│           ├── splash_screen.py
│           ├── home_screen.py
│           ├── live_monitor_screen.py
│           ├── band_analysis_screen.py
│           ├── session_screen.py
│           ├── summary_screen.py
│           ├── report_screen.py
│           ├── history_screen.py
│           └── settings_screen.py
├── models/
│   └── trained_rf_model.joblib
├── tests/
│   ├── test_signal_processing.py
│   ├── test_classification.py
│   ├── test_database.py
│   └── test_reporting.py
├── scripts/
│   ├── train_ml_model.py
│   └── build_executable.py
└── docs/
```

---

## Limitations

1. **Synthetic signals only:** This prototype does NOT acquire real human EEG data. All signals are mathematically generated.
2. **No clinical validation:** Classification rules and ML model are trained on synthetic data. Results have no clinical significance.
3. **Single-channel simulation:** Real EEG uses 19–256 electrodes; this prototype simulates a single-channel composite signal.
4. **Simplified frequency bands:** Real EEG analysis includes additional bands (Gamma, sub-bands) and spatial analysis.

---

## Future Work

- Integration with real EEG acquisition hardware (OpenBCI, Muse)
- Multi-channel electrode montage support (10-20 system)
- Event-Related Potential (ERP) analysis
- Deep learning classifiers (CNN, LSTM) on time-series data
- Real-time brain-computer interface (BCI) control applications
- HIPAA-compliant patient data management
- Cloud-based collaborative analysis platform

---

## License

MIT License — See [LICENSE](LICENSE) for details.

---

*Built as a Biomedical Engineering capstone prototype demonstrating EEG signal processing, spectral analysis, and cognitive classification concepts.*
