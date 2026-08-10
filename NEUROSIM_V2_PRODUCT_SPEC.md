# NeuroSim 2.0 — Complete Product Specification

## 1. Product Vision & Executive Overview
NeuroSim 2.0 is a professional desktop EEG / BCI (Brain-Computer Interface) cognitive-load analysis and signal simulation application. Built with Python and PySide6 (Qt), it provides continuous real-time signal acquisition, quantitative digital signal processing (DSP), frequency-domain spectral analysis, signal quality evaluation, machine-learning cognitive-load classification, persistent session history, and automated PDF report generation.

Every numerical metric, waveform plot, and cognitive load score displayed in the application is derived deterministically from underlying time-series data, mathematical DSP algorithms, and application state—ensuring absolute scientific integrity without superficial UI mockups or ungrounded statistics.

---

## 2. Core Product Capabilities (20 Features)
1. **Synthetic EEG Waveform Generation**: Configurable 4-band multi-frequency waveform synthesis (Delta, Theta, Alpha, Beta) with additive Gaussian noise and random seed determinism.
2. **Real-Time Signal Acquisition**: Continuous 250 Hz data ingestion via thread-safe rolling buffers.
3. **Generic Hardware Abstraction**: Transport-agnostic adapter interface for ESP32 USB Serial, ESP32 Wi-Fi, and future EEG hardware peripherals.
4. **Signal Quality Subsystem**: Continuous real-time quality scoring (`NO_SIGNAL`, `INSUFFICIENT_DATA`, `POOR`, `FAIR`, `GOOD`, `EXCELLENT`) based on amplitude boundaries, clipping detection, sequence continuity, and signal-to-noise ratio (SNR).
5. **Live Multi-Channel & Single-Channel Waveform Display**: High-performance scrolling time-series visualization.
6. **Digital Filtering Pipeline**: Butterworth bandpass filtering (0.5 – 30 Hz) and configurable notch filtering (50 Hz / 60 Hz) for powerline interference rejection.
7. **Fast Fourier Transform (FFT) & Welch PSD Analysis**: Power Spectral Density estimation using Welch's averaged periodogram with Hanning windowing.
8. **Quantitative Frequency Band Analysis**: Precise power integration across Delta (0.5–4 Hz), Theta (4–8 Hz), Alpha (8–13 Hz), and Beta (13–30 Hz) bands.
9. **Band-Power Ratio Metrics**: Quantitative calculation of Theta/Beta Ratio (TBR), Alpha/Beta Ratio (ABR), and (Theta+Alpha)/Beta Ratio for cognitive workload indices.
10. **Dual-Model Cognitive Load Classification**: Real-time evaluation combining rule-based clinical heuristics with a trained Random Forest machine learning classifier.
11. **Real-Time Telemetry & Performance Metrics**: Active sampling rate monitoring, packet drop percentage, sequence gap count, and latency tracking.
12. **Session Recording Engine**: Deterministic session lifecycle control with event marker tagging (e.g., baseline, task start, mental stressor, recovery).
13. **Session History Archive**: Searchable database archive of recorded EEG sessions with historical metric retrieval.
14. **Quantitative Analytics Dashboard**: Multi-view comparative analytical visualization across baseline vs. active workload phases.
15. **Automated PDF Report Exporter**: Production-grade ReportLab PDF document generator generating executive summaries, PSD charts, band ratios, and cognitive classification results.
16. **Hardware Diagnostics & Connection Control Center**: Unified transport status monitoring (`IDLE`, `SCANNING`, `CONNECTING`, `CONNECTED`, `STREAMING`, `ERROR`).
17. **Calibration & Baseline Profiling**: 60-second resting-state baseline capture for normalized z-score relative power analysis.
18. **Centralized Configuration Management**: Authoritative application config controlling sampling rates, filter parameters, PSD window sizes, and classification thresholds.
19. **Professional Dark & Glassmorphic Desktop UX**: High-contrast, responsive desktop layout optimized for high-resolution monitors.
20. **Extensible External Device Architecture**: Clean layer separation allowing future hardware sources to plug in without modifying downstream DSP or UI layers.

---

## 3. Mathematical Signal Processing Specification

### 3.1 Time-Domain Signals
Given a sampling frequency $f_s = 250\text{ Hz}$, the sampling interval is $\Delta t = \frac{1}{f_s} = 0.004\text{ seconds}$ (4 ms).
A time-series sample vector $\mathbf{x} = [x_0, x_1, \dots, x_{N-1}]$ of length $N$ represents microvolt $(\mu\text{V})$ amplitudes.

### 3.2 Butterworth Bandpass Filtering
A $4^{\text{th}}$-order Butterworth bandpass filter with cutoff frequencies $f_{\text{low}} = 0.5\text{ Hz}$ and $f_{\text{high}} = 30\text{ Hz}$ is applied using second-order sections (SOS):
$$\mathbf{y}[n] = \text{Bandpass}(\mathbf{x}[n], 0.5, 30.0, f_s)$$

### 3.3 Power Spectral Density (Welch's Method)
Welch PSD computes the spectral power $P(f)$ by segmenting $\mathbf{y}[n]$ into overlapping windows (Hanning window of length $N_{\text{fft}} = 256$, $50\%$ overlap):
$$P(f) = \frac{1}{M \sum_{n=0}^{L-1} w^2[n]} \sum_{m=0}^{M-1} \left| \sum_{n=0}^{L-1} y_m[n] w[n] e^{-j 2\pi f n / f_s} \right|^2$$

### 3.4 Absolute Band Power (ABP)
Integrated power within frequency boundary $[f_a, f_b]$:
$$\text{ABP}_{\text{band}} = \int_{f_a}^{f_b} P(f) \, df \approx \sum_{f = f_a}^{f_b} P(f) \cdot \Delta f$$
- **Delta Power**: $0.5 \text{ Hz} \le f < 4.0 \text{ Hz}$
- **Theta Power**: $4.0 \text{ Hz} \le f < 8.0 \text{ Hz}$
- **Alpha Power**: $8.0 \text{ Hz} \le f < 13.0 \text{ Hz}$
- **Beta Power**: $13.0 \text{ Hz} \le f < 30.0 \text{ Hz}$
- **Total Power**: $P_{\text{total}} = \text{ABP}_{\text{delta}} + \text{ABP}_{\text{theta}} + \text{ABP}_{\text{alpha}} + \text{ABP}_{\text{beta}}$

### 3.5 Relative Band Power (RBP)
$$\text{RBP}_{\text{band}} = \frac{\text{ABP}_{\text{band}}}{P_{\text{total}}} \times 100\%$$

### 3.6 Band Power Ratios
- **Theta / Beta Ratio (TBR)**: $\text{TBR} = \frac{\text{ABP}_{\text{theta}}}{\text{ABP}_{\text{beta}}}$ (Indicator of executive attention & ADHD/drowsiness)
- **Alpha / Beta Ratio (ABR)**: $\text{ABR} = \frac{\text{ABP}_{\text{alpha}}}{\text{ABP}_{\text{beta}}}$ (Indicator of relaxation vs. alertness)
- **Engagement Index (EI)**: $\text{EI} = \frac{\text{ABP}_{\text{beta}}}{\text{ABP}_{\text{alpha}} + \text{ABP}_{\text{theta}}}$ (Indicator of active mental workload)

---

## 4. Cognitive Load Classification Engine
The Cognitive Load Engine evaluates quantitative EEG features using a two-tier classification architecture:

1. **Rule-Based Heuristic Classifier**:
   - Evaluates TBR and Engagement Index against clinical thresholds.
   - Outputs: `LOW` (Relaxed state, high Alpha/low Beta), `OPTIMAL` (Focused state, elevated Beta & Engagement Index), `HIGH` (Cognitive overload / fatigue, high TBR & excessive Beta).
2. **Machine Learning Classifier (Random Forest)**:
   - Input vector: $\mathbf{f} = [\text{RBP}_{\text{delta}}, \text{RBP}_{\text{theta}}, \text{RBP}_{\text{alpha}}, \text{RBP}_{\text{beta}}, \text{TBR}, \text{ABR}, \text{EI}, \text{Mean}_{\text{amp}}, \text{Std}_{\text{amp}}]$.
   - Output: Predicted class (`LOW`, `MODERATE`, `HIGH`, `EXTREME`) with prediction probability confidence score ($0.0 \text{ to } 1.0$).

---

## 5. Signal Quality Subsystem
Continuously evaluates incoming frames and assigns an overall quality classification:
- **`NO_SIGNAL`**: Buffer empty or 0 samples received over $\ge 2.0\text{ seconds}$.
- **`INSUFFICIENT_DATA`**: Buffer contains $< 250$ samples ($< 1.0\text{ second}$).
- **`POOR`**: Amplitude clipping ($> 100\,\mu\text{V}$), excessive variance, or sequence packet loss $> 10\%$.
- **`FAIR`**: Minor noise or sequence loss between $2\% - 10\%$.
- **`GOOD`**: SNR $> 15\text{ dB}$, packet loss $< 2\%$, normal amplitude range ($10 - 80\,\mu\text{V}$).
- **`EXCELLENT`**: Clean waveform, zero packet drops, steady 250 Hz sampling, high spectral SNR.

---

## 6. Session Lifecycle & Persistence Model
Session State Machine:
`IDLE` $\rightarrow$ `PREPARING` $\rightarrow$ `RECORDING` $\rightarrow$ `PAUSED` $\rightarrow$ `STOPPING` $\rightarrow$ `COMPLETED` $\rightarrow$ `ERROR`

Database Schema (`sqlite3` in `neurosim_history.db`):
- `sessions`: `session_id`, `start_time`, `end_time`, `duration_sec`, `source_type`, `sampling_rate`, `channel_count`, `notes`.
- `session_metrics`: `metric_id`, `session_id`, `timestamp`, `delta_power`, `theta_power`, `alpha_power`, `beta_power`, `tbr`, `abr`, `cognitive_state`, `confidence`.
- `session_events`: `event_id`, `session_id`, `timestamp`, `event_type`, `event_description`.

---

## 7. Professional UI/UX Navigation Structure
1. **Overview / Dashboard**: System status, live cognitive load dial, active session summary, high-level metrics.
2. **Live Monitor**: Continuous scrolling time-series waveform viewer, real-time PSD curve, active frequency band power bars.
3. **Signal Lab**: Raw vs. filtered signal comparison, Butterworth filter settings, notch filter toggle, spectrum analyzer.
4. **Band Analysis**: Detailed Delta, Theta, Alpha, Beta power breakdown, relative power pie charts, TBR history curve.
5. **Experiments & Session Control**: Session recording start/pause/stop controls, event marker injection buttons, live annotation log.
6. **Session Compare**: Side-by-side comparison of 2 historical sessions or Baseline vs. Stressor phases.
7. **Reports & AI**: Automated report preview, AI summary generation, PDF exporter button.
8. **Validation Center**: Real-time signal validation tests, sampling frequency stability check, FFT numerical benchmark.
9. **Architecture & Diagnostics**: System layer topology view, active thread telemetry, buffer capacity graph.
10. **History Archive**: Searchable historical session data table with CSV/PDF export options.
11. **Hardware Connection Center**: Device scanner, port configuration, transport status badges.
12. **Settings**: Configurable sampling rates, band cutoff boundaries, UI refresh rates, database maintenance.

---

## 8. Security & Scientific Integrity Principles
- **No Fabricated Telemetry**: Hardware badges show `DISCONNECTED` when no source is connected; zero synthetic data is injected unless explicitly user-activated.
- **Deterministic Simulation**: Synthetic generator produces repeatable output when supplied with an explicit integer seed.
- **Non-Clinical Disclaimer**: All reports and UI screens include clear disclaimers stating that NeuroSim 2.0 is an engineering & research tool, not a medical diagnostic device.
