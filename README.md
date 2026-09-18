# Brain-Computer Interface (BCI) & EEG Cognitive Load Analysis Platform

[![Platform: Web Application](https://img.shields.io/badge/Platform-Web%20Application%20%28HTML5%20%2F%20Canvas%20%2F%20JS%29-0EA5E9.svg)](http://localhost:8000)
[![Hardware: Direct Laptop Wi-Fi](https://img.shields.io/badge/Hardware-Direct%20Laptop%20Wi--Fi%20%28UDP%205005%29-10B981.svg)]()
[![Automated Tests](https://img.shields.io/badge/Tests-15%2F15%20Passed-10B981.svg)]()
[![Database: SQLite WAL](https://img.shields.io/badge/Database-SQLite%20Indexed%20WAL-3B82F6.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

> **NeuroSim** is a real-time Brain-Computer Interface (BCI) and electroencephalogram (EEG) analytics web platform. It captures microvolt telemetry directly from acquisition hardware over local Wi-Fi, computes continuous Fourier spectral power densities in the browser, maps 2D anatomical brain potentials across the 10-20 international system, classifies cognitive workload states (Low, Moderate, High), and generates printable clinical research reports.

---

## Table of Contents

- [Project Overview & Purpose](#project-overview--purpose)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Signal Processing Pipeline](#signal-processing-pipeline)
- [User Authentication & Security](#user-authentication--security)
- [Data Governance, Privacy & Compliance](#data-governance-privacy--compliance)
- [Hardware Setup & ESP32 Pinout](#hardware-setup--esp32-pinout)
- [Getting Started](#getting-started)
- [Verification & Automated Test Results](#verification--automated-test-results)
- [Repository Structure](#repository-structure)
- [Research Scope & Disclaimer](#research-scope--disclaimer)
- [License](#license)

---

## Project Overview & Purpose

### What is Built
A complete, browser-based clinical and research workstation for processing and analyzing real-time EEG brainwave signals without third-party cloud dependencies or specialized desktop software installations.

### What It is Used For
1. **Real-Time Neurological Monitoring**: Streams scalp voltage signals at a standard medical acquisition rate of **250 Hz** with sub-10ms display latency.
2. **Frequency Rhythm Decomposition**: Separates composite analog EEG signals into four standard physiological bands:
   - **Delta (0.5 - 4 Hz)**: Deep restorative baseline, cortical deceleration.
   - **Theta (4 - 8 Hz)**: Drowsiness, working memory access, meditative states.
   - **Alpha (8 - 13 Hz)**: Sensory idling, calm attentiveness, relaxed alertness.
   - **Beta (13 - 30 Hz)**: Active cognition, logical problem solving, cognitive stress.
3. **Cognitive Load & Mental Stress Assessment**: Computes validated clinical neuromarkers:
   - **Spectral Stress Index (SSI)**: Ratio of high-frequency excitation to low-frequency relaxation ($\frac{\beta}{\alpha + \theta}$).
   - **Theta/Beta Ratio (TBR)**: Marker for attentional capacity and cognitive exhaustion ($\frac{\theta}{\beta}$).
   - **Alpha/Beta Ratio (ABR)**: Index balancing relaxation versus active processing ($\frac{\alpha}{\beta}$).
4. **2D Continuous Topographic Brain Mapping**: Continuously interpolates voltage distribution across 8 international 10-20 electrode positions (`Fp1`, `Fp2`, `C3`, `C4`, `P3`, `P4`, `O1`, `O2`).
5. **Dual-Model Cognitive State Classification**: Evaluates cognitive workload simultaneously using:
   - An **Ensemble Machine Learning Decision Forest** providing probability distributions $P(\text{LOW}), P(\text{MODERATE}), P(\text{HIGH})$ and statistical confidence.
   - A **Rule-Based Clinical Decision Support Engine** evaluating physiological heuristic boundary margins.
   - Automated conflict detection when models diverge.
6. **Clinical Report Generation**: Produces formatted printable PDF clinical records with session summaries, spectral metrics, and automated interpretation.

---

## Technology Stack

| Layer | Technology | Details |
|---|---|---|
| **Frontend UI & Visuals** | HTML5, CSS3, ES6+ JavaScript | High-contrast dark clinical theme, 60 FPS requestAnimationFrame canvas |
| **DSP Engine** | Pure JavaScript | In-place Radix-2 Cooley-Tukey FFT ($N=512$), Welch periodogram with 50% overlap, 4th-order Butterworth bandpass filter ($0.5-40$ Hz), 50Hz/60Hz notch filter ($Q=30$) |
| **Spatial Topography** | HTML5 2D Canvas Context | Continuous 2D Shepard's Inverse Distance Weighting (IDW) interpolation |
| **Audio Feedback** | Web Audio API | Pitch-modulated auditory neurofeedback tone tracking alpha synchrony |
| **Backend & Networking** | Python 3.10+ | Threaded HTTP server, UDP datagram socket listener, WebSocket server |
| **Hardware Telemetry** | UDP Sockets | Port 5005 listener with 2MB `SO_RCVBUF` socket buffer preventing OS packet loss |
| **Real-Time Relay** | WebSockets (`websockets`) | Port 8765 high-throughput 200 Hz batching relay with 3-second heartbeat |
| **Database** | SQLite 3 | WAL mode (Write-Ahead Logging), connection pooling, B-tree indexes |
| **Authentication** | Python `secrets`, CSPRNG | 6-digit One-Time Password (OTP) validation with 24-byte bearer tokens |
| **Hardware Firmware** | C++ / Arduino | ESP32 DevKit V1 dual-core microcontroller with 12-bit SAR ADC channels |

---

## System Architecture

```text
[ESP32 EEG Hardware]
        │
        │ 250 Hz UDP Datagrams (SAMPLE,<val>,<seq>,<checksum>)
        ▼
[server.py UDP Listener :5005]  ─── 2MB SO_RCVBUF Buffer (Lossless Ingestion)
        │
        │ Thread-Safe Queue
        ▼
[WebSocket Relay :8765]         ─── Real-Time Push with 3s Heartbeat
        │
        ▼
[Browser Client: web/app.js]
        ├── 20 Hz DSP Precision Loop
        │     ├── Zero-Phase 4th-Order Butterworth Filter (0.5 - 40 Hz)
        │     ├── 50 Hz / 60 Hz Notch Filter (Q = 30)
        │     ├── Radix-2 Cooley-Tukey FFT (N = 512, 0.488 Hz Resolution)
        │     ├── Welch 50% Overlap Periodogram Spectral Averaging
        │     ├── Trapezoidal Band Power Integration (Delta, Theta, Alpha, Beta)
        │     └── Dual Classification (Machine Learning Ensemble vs Clinical CDS)
        │
        ├── 60 FPS Rendering Loop
        │     ├── Oscilloscope Waveform Canvas (Microvolt Graticule)
        │     ├── Welch PSD Spectrum Canvas (0 - 40 Hz)
        │     └── Continuous 2D Topographic Heatmap Canvas (Shepard's IDW)
        │
        └── REST API Client (Port 8000)
              ├── OTP Researcher Login & Session Token Handling
              ├── Paginated Session Archive & Indexed Queries
              ├── RFC 4180 CSV and JSON Telemetry Downloads
              └── System Health Monitoring & Disaster Recovery
```

---

## Signal Processing Pipeline

### 1. Radix-2 Cooley-Tukey Fast Fourier Transform (FFT)
The discrete Fourier transform is computed using a Radix-2 decimation-in-time Cooley-Tukey algorithm ($N=512$ points):

$$X[k] = \sum_{n=0}^{N/2-1} x[2n] W_N^{2nk} + W_N^k \sum_{n=0}^{N/2-1} x[2n+1] W_N^{2nk}, \quad W_N = e^{-j \frac{2\pi}{N}}$$

- Frequency resolution: $\Delta f = \frac{f_s}{N} = \frac{250}{512} \approx 0.488\text{ Hz}$.
- Pre-computed bit-reversal indexing and twiddle factor tables eliminate all runtime trigonometric calculations.

### 2. Welch Periodogram Spectral Estimation
Reduces spectral noise variance by dividing circular 1250-sample buffers into 512-point sub-windows with 50% overlap:
- Each window is shaped using symmetric Hann coefficients: $w[n] = 0.5(1 - \cos(2\pi n / (N-1)))$.
- Individual periodograms are averaged to yield stable Power Spectral Density ($\mu\text{V}^2/\text{Hz}$).

### 3. Continuous 2D Brain Topography (Shepard's IDW)
Calculates continuous scalp voltage distribution across the 8 standard 10-20 electrode sites (`Fp1`, `Fp2`, `C3`, `C4`, `P3`, `P4`, `O1`, `O2`):

$$V(x, y) = \frac{\sum_{i=1}^8 \frac{V_i}{(d_i^2 + \epsilon)}}{\sum_{i=1}^8 \frac{1}{(d_i^2 + \epsilon)}}$$

---

## User Authentication & Security

The platform includes an integrated authentication workflow tailored for clinical research environments:

- **Login Modal**: Prompts the researcher for **Full Name**, **Institutional Email**, and **Mobile Number**.
- **One-Time Password (OTP) Generation**:
  - `POST /api/auth/send-otp` generates a secure 6-digit verification code with a 5-minute expiration.
  - In development mode, the active code is displayed directly in the user interface for testing.
- **Verification & Token Issuance**:
  - `POST /api/auth/verify-otp` validates the code and issues a 24-byte cryptographically secure session token.
  - The token is saved in `localStorage` and sent via `Authorization: Bearer <token>` on protected requests.
- **Automatic Hardware Connection**:
  - Upon successful verification, the modal closes and the client connects directly to the laptop's Wi-Fi telemetry stream (`ws://localhost:8765`).

---

## Data Governance, Privacy & Compliance

The application contains dedicated, self-contained compliance and operational pages:

1. **Privacy Policy ([`web/privacy.html`](web/privacy.html))**:
   - Outlines electrophysiological biometric data handling.
   - Complies with HIPAA and GDPR data governance principles.
   - Explicitly confirms all telemetry stays on the local host machine with **zero external data harvesting**.
2. **Terms of Service ([`web/terms.html`](web/terms.html))**:
   - Formal medical device disclaimer: strictly for research and academic demonstration.
   - Electrical safety requirements: mandates battery power or IEC 60601-1 galvanic isolation barriers when connecting custom scalp electrodes.
3. **Custom 404 Page ([`web/404.html`](web/404.html))**:
   - Handles missing routes with status code 404, diagnostic messaging, and one-click return to the workstation.
4. **Cookie & Telemetry Consent Banner**:
   - Persistent banner informing researchers of local-storage usage for session tokens and DSP filter states.
5. **Platform Meta & Directives**:
   - Search crawler directives ([`web/robots.txt`](web/robots.txt)), site map ([`web/sitemap.xml`](web/sitemap.xml)), and vector SVG icon ([`web/favicon.svg`](web/favicon.svg)).

---

## Hardware Setup & ESP32 Pinout

Upload the Wi-Fi telemetry firmware to your ESP32 DevKit V1:  
[`firmware/esp32/neurosim_wifi_esp32.ino`](firmware/esp32/neurosim_wifi_esp32.ino)

### ESP32 Pinout Configuration

| Channel | Target Waveform | ESP32 GPIO Pin | ADC Channel | Analog Voltage Range |
|---|---|---|---|---|
| **Channel 1** | **Delta (0.5 - 4 Hz)** | **GPIO 34** | ADC1_CH6 | `0.00V - 3.30V` (12-bit SAR ADC, 0-4095) |
| **Channel 2** | **Theta (4 - 8 Hz)** | **GPIO 35** | ADC1_CH7 | `0.00V - 3.30V` (12-bit SAR ADC, 0-4095) |
| **Channel 3** | **Alpha (8 - 13 Hz)** | **GPIO 32** | ADC1_CH4 | `0.00V - 3.30V` (12-bit SAR ADC, 0-4095) |
| **Channel 4** | **Beta (13 - 30 Hz)** | **GPIO 33** | ADC1_CH5 | `0.00V - 3.30V` (12-bit SAR ADC, 0-4095) |

### UDP Datagram Protocol

Packets stream over Wi-Fi directly to the laptop's IP address on UDP port `5005`:

$$\text{SAMPLE},<\text{microvolts}>,<\text{sequence}>,<\text{checksum}>$$

**Checksum Verification**:
$$\text{checksum} = (\text{sequenceNumber} + \lfloor|\text{waveform}| \times 100\rfloor) \pmod{256}$$

---

## Getting Started

### Prerequisites
- Python 3.10 or higher
- Modern web browser (Chrome, Edge, Firefox, or Safari)
- `websockets` Python package (`pip install websockets`)

### 1. Launch the Server

```powershell
python server.py
```

The server automatically detects your active network adapter and displays connection parameters:

```text
============================================================================
  [NEUROSIM] REAL-TIME EEG COGNITIVE ANALYTICS PLATFORM
============================================================================
  Web Application:         http://localhost:8000
  Laptop Wi-Fi Web URL:    http://192.168.29.155:8000
  Hardware UDP Stream:     192.168.29.155:5005 (UDP)
  WebSocket Real-Time Hub: ws://localhost:8765
  Health Check:            http://localhost:8000/api/health
  Database Engine:         SQLite WAL (db/neurosim.db)
  CSV Telemetry Export:    http://localhost:8000/api/export/csv
  JSON Telemetry Export:   http://localhost:8000/api/export/json
============================================================================
```

### 2. Access the Application

Open your browser to **[http://localhost:8000](http://localhost:8000)**.  
Complete the researcher login dialog (Name, Email, Mobile) to unlock the live workstation.

---

## Verification & Automated Test Results

The platform includes a comprehensive automated test suite verifying all layers of the system.

### Run All Test Suites:

```powershell
python -m unittest tests/test_dsp_mathematics.py tests/test_high_throughput_stream.py tests/test_websocket_stream.py tests/test_wifi_web_server.py tests/test_production_hardening.py
```

### Verification Matrix (15/15 Tests Passed):

| Test Suite | Subsystem Tested | Benchmark Criteria | Result | Status |
|---|---|---|---|---|
| `test_dsp_mathematics.py` | Radix-2 FFT Numerical Accuracy | Frequency peak error $< 0.5$ Hz | Verified on 2, 6, 10, 20 Hz tones | **PASS** |
| `test_dsp_mathematics.py` | Shepard's 2D IDW Interpolation | Continuous potential calculation | $49.98\ \mu\text{V}$ (Target $50.0\ \mu\text{V}$) | **PASS** |
| `test_dsp_mathematics.py` | UDP Checksum Check | Modulo-256 integrity check | Verified: `184` | **PASS** |
| `test_high_throughput_stream.py`| 250 Hz UDP Stream Receiver | Packet drop rate $< 0.5\%$ | 500 packets, **0.0% drop rate** | **PASS** |
| `test_high_throughput_stream.py`| Telemetry Exporter | RFC 4180 CSV and JSON | Validated: 501 rows / 500 items | **PASS** |
| `test_websocket_stream.py` | UDP to WebSocket Relay | Real-time bridge latency | Dispatched and parsed in $<10$ ms | **PASS** |
| `test_wifi_web_server.py` | REST API Status | `/api/status` response | Confirmed network IPs and ports | **PASS** |
| `test_wifi_web_server.py` | Hardware State Transition | Automatic live detection | State switches to connected | **PASS** |
| `test_production_hardening.py` | SQLite Indexes & Schema | WAL mode, 5 B-tree indexes | All tables and query indexes verified | **PASS** |
| `test_production_hardening.py` | OTP Authentication Flow | Send, verify, and CSPRNG token | Complete lifecycle validated | **PASS** |
| `test_production_hardening.py` | Sliding-Window Rate Limiting | 120 req/min per IP threshold | Over-quota bursts blocked (429) | **PASS** |
| `test_production_hardening.py` | Idempotency Deduplication | Prevent duplicate records | Replayed without duplicate rows | **PASS** |
| `test_production_hardening.py` | Database Disaster Recovery | Online atomic backup and restore | 61,440-byte snapshot validated | **PASS** |
| `test_production_hardening.py` | Health Check & 404 Route | `/api/health` and custom 404 | Healthy JSON and custom 404 page | **PASS** |
| `test_production_hardening.py` | Multi-User Concurrency | 12 simultaneous threads | Zero deadlock, 100% successful | **PASS** |

---

## Repository Structure

```text
NeuroSim/
├── server.py                        # Master Wi-Fi UDP Receiver, WebSocket Hub, SQLite DB & Auth Gateway
├── serve_local.py                   # Local development launcher proxying to server.py
├── firmware/
│   └── esp32/
│       ├── neurosim_wifi_esp32.ino  # ESP32 DevKit V1 Direct Laptop Wi-Fi Telemetry Firmware
│       └── neurosim_esp32.ino       # Legacy USB Serial Firmware
├── web/                             # Standalone Web Application
│   ├── index.html                   # Single-Page Clinical & Research Workstation
│   ├── styles.css                   # High-Contrast Clinical Dark Stylesheet
│   ├── app.js                       # Radix-2 FFT DSP, 60 FPS Canvas, IDW Topo & OTP Auth Client
│   ├── pdf_export.js                # Medical Session Report PDF Generator
│   ├── 404.html                     # Custom 404 Route Not Found Page
│   ├── privacy.html                 # Clinical Privacy Policy (HIPAA / GDPR Compliance)
│   ├── terms.html                   # Research Terms of Service & Electrical Safety Guide
│   ├── favicon.svg                  # Vector EEG Waveform Favicon
│   ├── robots.txt                   # Search Engine Crawler Directives
│   ├── sitemap.xml                  # XML Sitemap
│   └── manifest.json                # Web Application Manifest
├── tests/                           # Automated Test Suites (15 Tests)
│   ├── test_dsp_mathematics.py      # Radix-2 FFT and Shepard IDW Mathematical Tests
│   ├── test_high_throughput_stream.py# 250 Hz UDP Stream Drop Rate Test (0% drop)
│   ├── test_websocket_stream.py     # Live UDP-to-WebSocket Relay Test
│   ├── test_wifi_web_server.py      # Wi-Fi UDP and Web API Automated Tests
│   └── test_production_hardening.py # SQLite Indexes, OTP Auth, Rate Limiting, Backup/Restore
├── db/                              # SQLite Database Directory (WAL Mode, Gitignored)
├── logs/                            # Server Request and Error Logs (Gitignored)
├── README.md                        # Master Project Documentation
└── requirements.txt                 # Python Dependencies
```

---

## Research Scope & Disclaimer

1. **Academic and Research Demonstration**: NeuroSim is designed for neurotechnology research, educational prototyping, and algorithm benchmarking. It is not certified as a medical diagnostic device under FDA 510(k), CE mark Class IIa/IIb, or equivalent medical regulations.
2. **Electrical Safety**: When connecting physical electrodes to human subjects, ensure appropriate galvanic isolation conforming to IEC 60601-1 standards or use battery-powered acquisition circuits to prevent ground loops and electrical hazards.

---

## License

This project is licensed under the **[MIT License](LICENSE)**.
