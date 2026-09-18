# ISO 14971:2019 Risk Management & FMEA Report
## NeuroSim Quantitative EEG Cognitive Analytics Workstation

**Document ID:** RMF-NEUROSIM-2026-001  
**Revision:** 2.0 (Medical-Grade Compliance Release)  
**Classification:** Class B Software as a Medical Device (SaMD)  
**Standard Compliance:** ISO 14971:2019, IEC 62304:2006+AMD1:2015, IEC 60601-2-26:2019  

---

### 1. Executive Summary & Scope
This Risk Management File documents the systematic identification, evaluation, risk mitigation, and residual risk acceptability analysis for the **NeuroSim Scientific EEG Cognitive Analytics & DSP Platform**. 

The scope covers:
1. Real-time electrophysiological telemetry acquisition over local 250 Hz UDP/WebSocket streams.
2. Digital signal processing pipelines (Butterworth IIR, Powerline Notch, Ocular/EMG Artifact Clamping).
3. Radix-2 Cooley-Tukey FFT & Welch PSD frequency estimation.
4. Deep Neural Network (443,972 parameters) cognitive state classification and XAI saliency feature attribution.
5. Standard clinical interoperability exports (EDF+ IEC 60601-2-26, HL7 FHIR R4 LOINC 28634-4).
6. 21 CFR Part 11 compliant tamper-evident audit logging.

---

### 2. Risk Management Methodology & Scoring Criteria

#### Severity (S) Scale
* **1 - Negligible:** Inconvenience or temporary annoyance; no clinical consequence.
* **2 - Minor:** Minor error in non-critical metrics; easily detected by operator.
* **3 - Moderate:** Misclassification of cognitive state or delayed assessment; temporary disruption without physical harm.
* **4 - Critical:** Erroneous clinical report leading to inappropriate clinical protocol or misdiagnosis of high stress/fatigue.
* **5 - Catastrophic:** Severe injury or patient fatality (non-applicable to non-invasive SaMD, but reserved for catastrophic system faults).

#### Occurrence (O) Scale
* **1 - Extremely Rare:** Probability < 10^-6 per operating hour.
* **2 - Remote:** Probability 10^-5 to 10^-6.
* **3 - Occasional:** Probability 10^-4 to 10^-5.
* **4 - Probable:** Probability 10^-3 to 10^-4.
* **5 - Frequent:** Probability > 10^-3.

#### Detection (D) Scale
* **1 - Almost Certain:** Automated pre-flight interlock or diagnostic alarm halts operation immediately.
* **2 - High:** Visible visual flag or banner alerts the clinician prior to report generation.
* **3 - Moderate:** Clinician detects anomaly upon examining raw waveform or spectral distribution.
* **4 - Low:** Difficult to detect during routine operation; requires manual log inspection.
* **5 - Undetectable:** Latent defect that produces plausible but false clinical outputs.

$$RPN = S \times O \times D$$

**Acceptability Thresholds:**
* RPN < 20: Broadly Acceptable (Green).
* 20 <= RPN <= 40: As Low As Reasonably Practicable (ALARP - Yellow).
* RPN > 40: Unacceptable; requires mandatory engineering risk mitigation (Red).

---

### 3. Failure Mode and Effects Analysis (FMEA) Matrix

| Hazard ID | Subsystem | Failure Mode | Clinical Effect | Pre-S | Pre-O | Pre-D | Pre-RPN | Risk Mitigation Measure | Post-S | Post-O | Post-D | Post-RPN | Residual Risk Status |
|---|---|---|---|:---:|:---:|:---:|:---:|---|:---:|:---:|:---:|:---:|:---:|
| **HAZ-001** | Lead Sensors (IEC 60601-2-26) | Electrode impedance > 5.0 kOhm or lead-off | Distorted spectral density; spurious high-frequency noise falsely classified as high workload | 4 | 4 | 3 | **48** | **IEC 60601-2-26 Pre-Flight Interlock (`src/processing/impedance_manager.py`):** Software halts recording unless all leads < 5.0 kOhm; visual channel map alerts clinician; requires signed Physician Override. | 2 | 2 | 1 | **4** | Acceptable |
| **HAZ-002** | Signal Acquisition | High-voltage ocular blink (EOG) or clenching (EMG) | Transient amplitude spikes (> 150 uV) artificially corrupt theta/beta ratio (TBR) | 3 | 4 | 3 | **36** | **Real-Time Artifact Clamping (`src/processing/artifact_filter.py`):** Online soft-saturation limiter clamps frontal EOG blinks and temporal EMG high-frequency bursts without phase distortion. | 2 | 2 | 1 | **4** | Acceptable |
| **HAZ-003** | Wi-Fi Telemetry Link | UDP packet loss or burst latency jitter | Discontinuous time-domain buffers causing spectral leakage in Welch PSD | 3 | 3 | 3 | **27** | **Circular Buffer Ingestion & Sequence Auditing (`server.py`):** Monotonic sequence number tracking, loss-rate telemetry badge, automatic jitter buffering at 250 Hz. | 2 | 1 | 2 | **4** | Acceptable |
| **HAZ-004** | AI Diagnostic Engine | DNN gradient saturation or distribution shift | Overconfident incorrect cognitive workload state prediction (> 99% certainty on noisy input) | 4 | 3 | 4 | **48** | **Pre-Softmax Saliency Feature Attribution (`src/classification/ai_report_model.py`):** Calculates partial logit / partial x to expose driving neuromarkers, dual heuristic/ML consensus banner, and explicit non-diagnostic SaMD disclaimer. | 2 | 2 | 2 | **8** | Acceptable |
| **HAZ-005** | Medical Data Storage | Unauthorized database alteration or session spoofing | Falsified research records or compromised clinical trial integrity | 4 | 2 | 4 | **32** | **21 CFR Part 11 SHA-256 Merkle Chain (`server.py`):** Immutable cryptographic forward hash chaining on every session commit with independent verification endpoint `/api/audit/verify`. | 2 | 1 | 1 | **2** | Acceptable |
| **HAZ-006** | Medical Interoperability | Non-standard or truncated EDF+ / FHIR data export | Inability of hospital PACS/EHR systems to import electrophysiological telemetry | 3 | 3 | 2 | **18** | **IEC 60601-2-26 EDF+ & HL7 FHIR R4 Bundle Validation (`src/reporting/`):** Strict 256-byte ASCII header enforcement, 16-bit PCM integer scaling, LOINC 28634-4 diagnostic resource compliance. | 2 | 1 | 1 | **2** | Acceptable |
| **HAZ-007** | Powerline Interference | 50 Hz / 60 Hz mains harmonic induction | Dominant peak falsely detected at line frequency overriding biological rhythms | 3 | 4 | 2 | **24** | **High-Q Biquad Notch Filter Pipeline (`web/app.js`):** Narrowband IIR notch with Q = 30 centered at 50 Hz and 60 Hz with user toggle and automatic frequency selection. | 1 | 2 | 1 | **2** | Acceptable |

---

### 4. Risk Mitigation Verification & Traceability

1. **Pre-Flight Impedance Gating (HAZ-001):**
   - Verified by unit test `tests.test_medical_grade_compliance.TestMedicalGradeCompliance.test_impedance_manager_thresholds_and_override`.
   - Result: All channels > 5.0 kOhm trigger interlock; recording blocked until `set_clinical_override()` is logged.
2. **Artifact Rejection (HAZ-002):**
   - Verified by unit test `tests.test_medical_grade_compliance.TestMedicalGradeCompliance.test_artifact_filter_ocular_and_emg_clamping`.
   - Result: EOG voltage spikes exceeding 150 uV are smoothly clamped to allowable boundaries; baseline rhythm preserved.
3. **Cryptographic Audit Chaining (HAZ-005):**
   - Verified by unit test `tests.test_medical_grade_compliance.TestMedicalGradeCompliance.test_audit_hash_chaining_and_tamper_detection`.
   - Result: Tampering with a single character in past records triggers immediate SHA-256 mismatch detection on verification.

---

### 5. Conclusion & Residual Risk Acceptance
All identified hazards have been mitigated through automated engineering controls, digital signal processing algorithms, and cryptographic verification mechanisms. All residual Risk Priority Numbers are below the acceptability threshold of RPN = 10.

The overall residual risk of the NeuroSim platform is determined to be **Broadly Acceptable** under ISO 14971:2019 for clinical research and cognitive workload analytics.
