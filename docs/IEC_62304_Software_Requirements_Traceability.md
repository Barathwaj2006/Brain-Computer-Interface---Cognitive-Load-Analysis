# IEC 62304:2006+AMD1:2015 Software Requirements Traceability Matrix
## NeuroSim Quantitative EEG Cognitive Analytics Workstation

**Document ID:** SRM-NEUROSIM-2026-002  
**Software Safety Classification:** Class B (Non-life-supporting diagnostic and monitoring SaMD)  
**Lifecycle Process:** IEC 62304 Section 5 (Software Development Process)  
**Traceability Coverage:** 100% Verification across System Requirements, Architecture, and Unit Tests  

---

### 1. Software Safety Classification Justification
According to IEC 62304 Section 4.3:
* **Class A:** No injury or damage to health is possible.
* **Class B:** Non-serious injury is possible.
* **Class C:** Death or serious injury is possible.

NeuroSim is designated **Class B Software as a Medical Device (SaMD)**. While non-invasive EEG monitoring does not directly deliver energy or medication, erroneous cognitive state classification or unnoticed lead detachment during safety-critical monitoring protocols (e.g. operator fatigue assessment) could theoretically contribute to clinical misjudgment if not caught by pre-flight quality checks and physician oversight.

---

### 2. Bidirectional Traceability Matrix

| Requirement ID | Specification Category | Requirement Statement | Architectural Module / Implementation File | Verification Test Case ID | Test Result |
|---|---|---|---|---|:---:|
| **SRS-MED-01** | Medical Interoperability | System shall export continuous multi-channel electrophysiological telemetry in standard European Data Format (EDF+) conforming to IEC 60601-2-26 and official EDF+ specification. | `src/reporting/edf_exporter.py`<br>`server.py` (`/api/export/edf`) | `tests.test_medical_grade_compliance.TestMedicalGradeCompliance.test_edf_binary_export_conformity` | **PASSED** |
| **SRS-MED-02** | Health Interoperability | System shall export quantitative EEG session metrics as an HL7 FHIR R4 JSON Bundle comprising a `DiagnosticReport` (LOINC 28634-4) and linked `Observation` resources. | `src/reporting/fhir_exporter.py`<br>`server.py` (`/api/fhir/DiagnosticReport`) | `tests.test_medical_grade_compliance.TestMedicalGradeCompliance.test_fhir_r4_bundle_export_conformity` | **PASSED** |
| **SRS-MED-03** | Data Integrity & Security | System shall maintain an immutable 21 CFR Part 11 compliant audit trail utilizing SHA-256 Merkle hash chaining with real-time tamper-detection verification. | `server.py` (`DatabaseManager.log_audit`, `verify_audit_chain`) | `tests.test_medical_grade_compliance.TestMedicalGradeCompliance.test_audit_hash_chaining_and_tamper_detection` | **PASSED** |
| **SRS-MED-04** | Sensor Quality Assurance | System shall track 10-20 electrode contact impedances continuously; recording shall be interlocked if any lead exceeds 5.0 kOhm unless authorized by a signed Physician Override. | `src/processing/impedance_manager.py`<br>`server.py` (`/api/telemetry/impedance`, `/api/clinical-override`) | `tests.test_medical_grade_compliance.TestMedicalGradeCompliance.test_impedance_manager_thresholds_and_override` | **PASSED** |
| **SRS-MED-05** | Physiological Artifact Rejection | System shall execute real-time online detection and suppression of high-amplitude ocular blinks (EOG) and temporal muscle bursts (EMG) without phase distortion. | `src/processing/artifact_filter.py`<br>`web/app.js` (`filterSample`) | `tests.test_medical_grade_compliance.TestMedicalGradeCompliance.test_artifact_filter_ocular_and_emg_clamping` | **PASSED** |
| **SRS-MED-06** | Explainable AI (XAI) | Clinical report engine shall compute pre-softmax gradient sensitivities (partial logit / partial feature) identifying top neuromarkers driving the 443,972-parameter DNN prediction. | `src/classification/ai_report_model.py` (`compute_saliency_map`)<br>`server.py` (`/api/ai-report`) | `tests.test_medical_grade_compliance.TestMedicalGradeCompliance.test_xai_saliency_attribution_computation` | **PASSED** |
| **SRS-DSP-01** | Digital Signal Processing | System shall execute 4th-order zero-phase Butterworth bandpass (0.5 - 40 Hz) and 50/60 Hz notch filtering on incoming 250 Hz telemetry. | `web/app.js` (`Radix2FFT`, `BiquadSection`) | `tests.test_dsp_mathematics.TestDSPMathematics.test_butterworth_coefficients` | **PASSED** |
| **SRS-DSP-02** | Frequency Estimation | Spectral analysis shall compute 50% overlapping Welch periodograms with Hann windowing achieving <= 0.5 Hz frequency resolution. | `web/app.js` (`executeWelchDSP`) | `tests.test_dsp_mathematics.TestDSPMathematics.test_welch_psd_accuracy` | **PASSED** |
| **SRS-NET-01** | Real-Time Telemetry | Telemetry gateway shall ingest UDP packets at 250 Hz with monotonic sequence validation, zero packet memory leaks, and jitter buffering. | `server.py` (`WiFiTelemetryServer`) | `tests.test_high_throughput_stream.TestHighThroughputStream.test_udp_throughput` | **PASSED** |

---

### 3. Software Architecture & Verification Strategy
```
+---------------------------------------------------------------------------------+
|                                 USER INTERFACE                                  |
|         Web Dashboard • Pre-Flight Interlock Modal • PDF Clinical Exporter       |
+---------------------------------------------------------------------------------+
                                      | HTTP/WS
+---------------------------------------------------------------------------------+
|                       NEUROSIM RUNTIME CORE (server.py)                         |
|   +-------------------------------------------------------------------------+   |
|   | 21 CFR Part 11 SHA-256 Audit Trail (DatabaseManager.log_audit)          |   |
|   +-------------------------------------------------------------------------+   |
|   | IEC 60601-2-26 Impedance QA & Physician Interlock (ImpedanceManager)    |   |
|   +-------------------------------------------------------------------------+   |
|   | Deep Neural Network AI Diagnostic Engine (443,972 Params + Saliency)    |   |
|   +-------------------------------------------------------------------------+   |
|   | Standard Exporters: EDF+ Binary (EDFExporter) | HL7 FHIR R4 (FHIRExporter)| |
|   +-------------------------------------------------------------------------+   |
|   | Physiological Artifact Filter (EOG / EMG Online Clamping)               |   |
|   +-------------------------------------------------------------------------+   |
+---------------------------------------------------------------------------------+
```

---

### 4. Verification Sign-Off
All 9 Software Requirement Specifications have been verified via automated deterministic test suites. Regression testing confirmed 100% test pass rate with zero safety anomalies detected.
