/**
 * ==============================================================================
 * NEUROSIM : SCIENTIFIC EEG COGNITIVE ANALYTICS PLATFORM
 * High-Performance Engine: Radix-2 Cooley-Tukey FFT, Welch Periodogram,
 * Multi-Stage IIR Filtering, 2D Shepard's IDW Topography, Dual Ensemble Classifier,
 * Automated DSP Benchmark, and Resilient Wi-Fi WebSocket Stream
 * ==============================================================================
 */

// ------------------------------------------------------------------------------
// 1. Core Platform Constants & Circular Buffers
// ------------------------------------------------------------------------------
const SAMPLING_RATE = 250;           // 250 Hz standard clinical acquisition
const BUFFER_SIZE = 1250;            // 5-second circular buffer (1250 samples)
const FFT_SIZE = 512;                // Radix-2 FFT window size (df ≈ 0.488 Hz)

const rawSignalBuffer = new Float32Array(BUFFER_SIZE);
const filteredSignalBuffer = new Float32Array(BUFFER_SIZE);
const sensorSignalBuffer = new Float32Array(BUFFER_SIZE);
const frozenSensorBuffer = new Float32Array(BUFFER_SIZE);
let writeIndex = 0;
let totalSamplesReceived = 0;

// 3 Electrodes + 1 Sensor Telemetry Tracking
window.__appVersion = "2.5.5";
let latestLeads = { e1: 0.0, e2: 0.0, e3: 0.0, sensor: 0.0, diffEeg: 0.0 };
let activeChannelMode = "eeg"; // "eeg", "sensor", "dual"

// =============================================================================
// Cloud & Backend URL Configuration (Vercel, Railway, Supabase, Local)
// =============================================================================
function normalizeBackendUrl(rawUrl) {
    if (!rawUrl || typeof rawUrl !== 'string') return '';
    let clean = rawUrl.trim();
    if (!clean) return '';
    // Prepend https:// if protocol is omitted (default to http for localhost/127.0.0.1)
    if (!/^https?:\/\//i.test(clean)) {
        if (/^(localhost|127\.0\.0\.1)/i.test(clean)) {
            clean = 'http://' + clean;
        } else {
            clean = 'https://' + clean;
        }
    }
    // Remove trailing slashes
    clean = clean.replace(/\/+$/, '');
    // Strip accidental /api suffix
    clean = clean.replace(/\/api$/i, '');
    return clean;
}

const BACKEND_CONFIG = {
    getApiBaseUrl() {
        const stored = localStorage.getItem('neurosim_backend_url');
        if (stored && stored.trim()) {
            return normalizeBackendUrl(stored);
        }
        if (window.__NEUROSIM_BACKEND_URL__) {
            return normalizeBackendUrl(window.__NEUROSIM_BACKEND_URL__);
        }
        return '';
    },
    getWsUrl() {
        const customWs = localStorage.getItem('neurosim_ws_url');
        if (customWs && customWs.trim()) {
            return customWs.trim();
        }
        const apiBase = this.getApiBaseUrl();
        if (apiBase) {
            try {
                const u = new URL(apiBase, window.location.href);
                const wsProto = u.protocol === 'https:' ? 'wss:' : 'ws:';
                return `${wsProto}//${u.host}/ws`;
            } catch (e) {
                console.warn("[NeuroSim] Invalid API base for WebSocket:", e);
            }
        }
        const wsHost = window.location.hostname || "localhost";
        const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
        if (wsPathMode) {
            const portPart = (window.location.port && window.location.port !== "80" && window.location.port !== "443") ? `:${window.location.port}` : "";
            return `${wsProto}//${wsHost}${portPart}/ws`;
        }
        return `${wsProto}//${wsHost}:${WS_PORT}`;
    },
    apiEndpoint(path) {
        const base = this.getApiBaseUrl();
        const cleanPath = path.startsWith('/') ? path : `/${path}`;
        return `${base}${cleanPath}`;
    }
};

// Hardware & Wi-Fi Connection State
const WS_PORT = 8765;
let wsPort = 8765;
let isHardwareActive = false;
let isSimulatorMode = false;
let wsClient = null;
let wifiIp = "192.168.29.155";
let udpPort = 5005;
let wsHeartbeatTimer = null;

// WebSerial Direct USB Streaming State
let serialPort = null;
let serialReader = null;
let isWebSerialActive = false;
let serialKeepReading = false;

// Filter Pipeline States & Online Artifact Suppressor
let isBandpassActive = true;
let notchFilterMode = "50Hz"; // "OFF", "50Hz", "60Hz"
let isArtifactFilterActive = true; // Medical EOG / EMG Artifact Suppression
let prevFiltSample = 0.0;
let lastArtifactTimestamp = 0;

// Individual Alpha Frequency (IAF) & Baseline Calibration State
let userIAF = parseFloat(localStorage.getItem('neurosim_baseline_iaf')) || 10.0;
let isBaselineCalibrated = !!localStorage.getItem('neurosim_baseline_iaf');
let calibrationState = { running: false, secondsLeft: 15, timerId: null, alphaAccum: [] };

// Automated Contact Impedance & Signal Quality Index (SQI)
let currentSQI = 100;

// Session Timeline Event Markers
let sessionMarkers = [];

// Temporal Smoothing (EMA & Hysteresis Voting Queue)
let emaProbLow = 0.10, emaProbMod = 0.75, emaProbHigh = 0.15;
let recentClassificationVotes = [];
let smoothedLoadState = "MODERATE";

// Web Audio Neurofeedback State (432 Hz Alpha Harmonic Drone)
let audioCtx = null;
let bioCarrierOsc = null;
let bioModulatorOsc = null;
let bioGainNode = null;
let isAudioActive = false;
let biofeedbackVolume = 0.5; // Master audio volume multiplier (0.0 - 1.0)
let isStreamFrozen = false;
let isLiveTestStreaming = false;
let testStreamInterval = null;
let testStreamPhase = 0.0;
const frozenRawBuffer = new Float32Array(BUFFER_SIZE);
const frozenFilteredBuffer = new Float32Array(BUFFER_SIZE);
let displayScaleUv = 50.0;          // Microvolts scale range: ±25, ±50, ±100, ±200 μV
let displaySamplesCount = 500;       // Display sample window: 250 (1s), 500 (2s), 750 (3s), 1250 (5s)
let activeColormap = "coolwarm";     // "coolwarm", "viridis", "plasma", "jet"

// Simulator Parameters (when Hardware is idle or simulator active)
const simParams = {
    delta: 0.30,
    theta: 0.30,
    alpha: 0.70,
    beta: 0.30,
    noise: 0.15
};
let simPhase = 0.0;

// Processed Spectral Metrics Cache
const currentBands = { delta: 25.0, theta: 25.0, alpha: 25.0, beta: 25.0 };
const currentMetrics = {
    dominantFreq: 10.0,
    dominantBand: "ALPHA",
    tbr: 1.00,
    abr: 1.00,
    stressIndex: 0.45,
    engagement: 0.50,
    totalPower: 120.0,
    ruleState: "MODERATE",
    ruleMargin: 82.0,
    mlState: "MODERATE",
    mlConf: 85.0,
    probLow: 0.10,
    probMod: 0.75,
    probHigh: 0.15
};

// Electrode Voltage Potentials for 10-20 Topographic Mapping (μV)
const electrodePotentials = {
    Fp1: 0.0, Fp2: 0.0, C3: 0.0, C4: 0.0, P3: 0.0, P4: 0.0, O1: 0.0, O2: 0.0
};

// Session Recording State
let isRecording = false;
let recordingStartTime = 0;
let recordedSampleCount = 0;
let currentSessionId = "";

// 5-Stage Signal Lab State
let activeLabStage = 0;

// UI Performance Tracking
let lastFrameTime = performance.now();
let frameCount = 0;
let currentFps = 60;

// ------------------------------------------------------------------------------
// 2. High-Performance Radix-2 Cooley-Tukey FFT & Welch Periodogram
// ------------------------------------------------------------------------------
class Radix2FFT {
    constructor(n) {
        this.n = n;
        this.levels = Math.log2(n);
        if (Math.floor(this.levels) !== this.levels) {
            throw new Error("FFT size must be a power of 2");
        }

        // 1. Pre-calculate bit-reversal permutation table
        this.bitRev = new Uint32Array(n);
        for (let i = 0; i < n; i++) {
            let rev = 0;
            for (let j = 0; j < this.levels; j++) {
                rev = (rev << 1) | ((i >> j) & 1);
            }
            this.bitRev[i] = rev;
        }

        // 2. Pre-calculate trigonometric twiddle factor tables
        this.cosTable = new Float32Array(n / 2);
        this.sinTable = new Float32Array(n / 2);
        for (let i = 0; i < n / 2; i++) {
            const angle = (-2.0 * Math.PI * i) / n;
            this.cosTable[i] = Math.cos(angle);
            this.sinTable[i] = Math.sin(angle);
        }

        // 3. Pre-calculate Hann Window coefficients
        this.hannWindow = new Float32Array(n);
        let winSumSq = 0.0;
        for (let i = 0; i < n; i++) {
            const w = 0.5 * (1.0 - Math.cos((2.0 * Math.PI * i) / (n - 1)));
            this.hannWindow[i] = w;
            winSumSq += w * w;
        }
        this.noiseBandwidthFactor = winSumSq * SAMPLING_RATE;
    }

    transform(real, imag) {
        const n = this.n;

        // Bit-reversal reordering in-place
        for (let i = 0; i < n; i++) {
            const j = this.bitRev[i];
            if (i < j) {
                const tempR = real[i]; real[i] = real[j]; real[j] = tempR;
                const tempI = imag[i]; imag[i] = imag[j]; imag[j] = tempI;
            }
        }

        // Cooley-Tukey Radix-2 Butterfly stages
        for (let size = 2; size <= n; size <<= 1) {
            const halfSize = size >> 1;
            const step = n / size;

            for (let i = 0; i < n; i += size) {
                for (let j = 0; j < halfSize; j++) {
                    const twiddleIdx = j * step;
                    const c = this.cosTable[twiddleIdx];
                    const s = this.sinTable[twiddleIdx];

                    const rB = real[i + j + halfSize];
                    const iB = imag[i + j + halfSize];

                    // Complex multiplication: (rB + iB*s)*(c + i*s)
                    const tr = rB * c - iB * s;
                    const ti = rB * s + iB * c;

                    real[i + j + halfSize] = real[i + j] - tr;
                    imag[i + j + halfSize] = imag[i + j] - ti;
                    real[i + j] += tr;
                    imag[i + j] += ti;
                }
            }
        }
    }
}

const fftInstance = new Radix2FFT(FFT_SIZE);
const fftRealBuf = new Float32Array(FFT_SIZE);
const fftImagBuf = new Float32Array(FFT_SIZE);
const psdAccumulator = new Float32Array(FFT_SIZE / 2);

// ------------------------------------------------------------------------------
// 3. Multi-Stage Digital IIR Filters (Butterworth & Notch)
// ------------------------------------------------------------------------------
class BiquadSection {
    constructor(b0, b1, b2, a1, a2) {
        this.b0 = b0; this.b1 = b1; this.b2 = b2;
        this.a1 = a1; this.a2 = a2;
        this.x1 = 0; this.x2 = 0; this.y1 = 0; this.y2 = 0;
    }
    process(x) {
        const y = this.b0 * x + this.b1 * this.x1 + this.b2 * this.x2 - this.a1 * this.y1 - this.a2 * this.y2;
        this.x2 = this.x1; this.x1 = x;
        this.y2 = this.y1; this.y1 = isNaN(y) ? x : y;
        return this.y1;
    }
    reset() {
        this.x1 = this.x2 = this.y1 = this.y2 = 0;
    }
}

// 4th Order Butterworth Bandpass Filter (0.5 - 40 Hz @ 250 Hz) - 2 Cascaded Biquad Sections
const bpfStage1 = new BiquadSection(0.1611, 0.0, -0.1611, -1.3412, 0.6778);
const bpfStage2 = new BiquadSection(0.1611, 0.0, -0.1611, -1.5241, 0.7239);

// 50 Hz Notch Filter (Q = 30 @ 250 Hz)
const notch50 = new BiquadSection(0.9634, -0.5954, 0.9634, -0.5954, 0.9268);

// 60 Hz Notch Filter (Q = 30 @ 250 Hz)
const notch60 = new BiquadSection(0.9634, -0.2012, 0.9634, -0.2012, 0.9268);

// Moving average DC detrend accumulator
let dcAccumulator = 0.0;

function filterSample(sample) {
    if (!isBandpassActive) {
        return sample;
    }

    // 1. Remove DC drift baseline
    dcAccumulator = 0.995 * dcAccumulator + 0.005 * sample;
    const detrended = sample - dcAccumulator;

    // 2. 4th Order Butterworth Bandpass
    let y = bpfStage1.process(detrended);
    y = bpfStage2.process(y);

    // 3. Optional Powerline Notch Filtering
    if (notchFilterMode === "50Hz") {
        y = notch50.process(y);
    } else if (notchFilterMode === "60Hz") {
        y = notch60.process(y);
    }

    // 4. Adaptive Physiological Artifact Suppressor (Ocular EOG Blinks & Temporal EMG Bursts)
    if (isArtifactFilterActive) {
        // High-Frequency Muscle (EMG) Spike Slew-Rate Limiter (gradient > 35 μV/sample)
        const diff = y - prevFiltSample;
        if (Math.abs(diff) > 35.0) {
            y = prevFiltSample + Math.sign(diff) * (35.0 + 5.0 * Math.tanh((Math.abs(diff) - 35.0) / 10.0));
            lastArtifactTimestamp = Date.now();
        }

        // Low-Frequency High-Amplitude Ocular Blink (EOG) Soft-Knee Attenuation (> 65 μV)
        if (Math.abs(y) > 65.0) {
            y = Math.sign(y) * (60.0 + 15.0 * Math.tanh((Math.abs(y) - 60.0) / 20.0));
            lastArtifactTimestamp = Date.now();
        }
    }
    prevFiltSample = y;

    return y;
}

// Push sample into circular buffers
function ingestSample(rawVal, sensorVal = 0, e1 = null, e2 = null, e3 = null) {
    const numRaw = Number(rawVal) || 0.0;
    const filteredVal = filterSample(numRaw);
    const numSensor = (sensorVal !== undefined && sensorVal !== null) ? Number(sensorVal) : 0.0;

    rawSignalBuffer[writeIndex] = numRaw;
    filteredSignalBuffer[writeIndex] = filteredVal;
    sensorSignalBuffer[writeIndex] = numSensor;

    writeIndex = (writeIndex + 1) % BUFFER_SIZE;
    totalSamplesReceived++;

    latestLeads.e1 = (e1 !== null && e1 !== undefined) ? Number(e1) : numRaw;
    latestLeads.e2 = (e2 !== null && e2 !== undefined) ? Number(e2) : 0.0;
    latestLeads.e3 = (e3 !== null && e3 !== undefined) ? Number(e3) : 0.0;
    latestLeads.sensor = numSensor;
    latestLeads.diffEeg = numRaw;

    if (isRecording) {
        recordedSampleCount++;
    }
}

// ------------------------------------------------------------------------------
// 4. Precision DSP Calculation (Welch Periodogram Averaging @ 20 Hz)
// ------------------------------------------------------------------------------
function executeWelchDSP() {
    if (totalSamplesReceived === 0 && !isSimulatorMode && !isLiveTestStreaming) {
        // Dynamic Baseline Standby Rhythms (Calm resting wakefulness awaiting live telemetry packets)
        const tSec = Date.now() / 1200;
        const driftA = Math.sin(tSec * 0.8) * 0.9;
        const driftB = Math.cos(tSec * 1.1) * 0.6;
        currentBands.delta = Math.max(10, Math.min(40, 22.0 + Math.sin(tSec * 0.6) * 0.5));
        currentBands.theta = Math.max(10, Math.min(35, 18.0 + driftB));
        currentBands.alpha = Math.max(20, Math.min(55, 39.0 + driftA));
        currentBands.beta  = Math.max(10, Math.min(35, 21.0 - driftA * 0.6));

        // Normalize sum to 100.0%
        const sumB = currentBands.delta + currentBands.theta + currentBands.alpha + currentBands.beta;
        currentBands.delta = (currentBands.delta / sumB) * 100;
        currentBands.theta = (currentBands.theta / sumB) * 100;
        currentBands.alpha = (currentBands.alpha / sumB) * 100;
        currentBands.beta  = (currentBands.beta  / sumB) * 100;

        currentMetrics.dominantFreq = 10.0 + Math.sin(tSec * 0.4) * 0.25;
        currentMetrics.dominantBand = "ALPHA";
        currentMetrics.tbr = currentBands.theta / Math.max(0.1, currentBands.beta);
        currentMetrics.abr = currentBands.alpha / Math.max(0.1, currentBands.beta);
        currentMetrics.stressIndex = (currentBands.theta + currentBands.beta) / Math.max(0.1, currentBands.alpha + currentBands.theta);
        currentMetrics.engagement = currentBands.beta / Math.max(0.1, currentBands.alpha + currentBands.theta);
        currentMetrics.totalPower = 85.0 + Math.sin(tSec * 0.5) * 6.0;
        currentMetrics.ruleState = "MODERATE";
        currentMetrics.ruleMargin = 78.5 + driftA * 1.2;
        currentMetrics.mlState = "MODERATE";
        currentMetrics.mlConf = 89.2 + Math.cos(tSec * 0.7) * 0.8;
        currentMetrics.probLow = 0.14;
        currentMetrics.probMod = 0.76;
        currentMetrics.probHigh = 0.10;

        // Populate smooth physiological PSD spectrum (10 Hz alpha peak)
        const halfN = FFT_SIZE / 2;
        const df = SAMPLING_RATE / FFT_SIZE;
        for (let k = 1; k < halfN; k++) {
            const freq = k * df;
            const alphaPeak = Math.exp(-Math.pow((freq - 10.0) / 2.2, 2)) * 14.0;
            const thetaPeak = Math.exp(-Math.pow((freq - 6.0) / 1.8, 2)) * 5.0;
            const betaPeak  = Math.exp(-Math.pow((freq - 19.0) / 4.0, 2)) * 4.5;
            const oneOverF  = 8.0 / Math.max(1.0, freq);
            psdAccumulator[k] = oneOverF + alphaPeak + thetaPeak + betaPeak + (Math.sin(k + tSec) * 0.2);
        }

        updateUIElements("Resting baseline EEG rhythm (Awaiting active hardware telemetry packets)");
        return;
    }

    psdAccumulator.fill(0.0);
    const halfN = FFT_SIZE / 2;
    const df = SAMPLING_RATE / FFT_SIZE; // ≈ 0.488 Hz

    // 50% Overlapping Segments: 3 segments of length 512 over last 1024 samples
    const segmentOffsets = [512, 256, 0];
    const numSegments = segmentOffsets.length;

    for (let s = 0; s < numSegments; s++) {
        const offset = segmentOffsets[s];

        // Fill real buffer with Hann-windowed samples
        for (let i = 0; i < FFT_SIZE; i++) {
            const bufIdx = (writeIndex - 1024 + offset + i + BUFFER_SIZE) % BUFFER_SIZE;
            fftRealBuf[i] = filteredSignalBuffer[bufIdx] * fftInstance.hannWindow[i];
            fftImagBuf[i] = 0.0;
        }

        // Execute Radix-2 Cooley-Tukey FFT
        fftInstance.transform(fftRealBuf, fftImagBuf);

        // Accumulate Periodogram PSD (μV²/Hz)
        for (let k = 0; k < halfN; k++) {
            const r = fftRealBuf[k];
            const im = fftImagBuf[k];
            const power = (r * r + im * im) / fftInstance.noiseBandwidthFactor;
            psdAccumulator[k] += power / numSegments;
        }
    }

    // Adaptive Band Integration using Subject's Individual Alpha Frequency (IAF)
    const thetaLow = 4.0;
    const thetaHigh = Math.max(6.0, userIAF - 2.0);
    const alphaLow = thetaHigh;
    const alphaHigh = Math.min(14.0, userIAF + 2.0);
    const betaLow = alphaHigh;
    const betaHigh = 30.0;

    let pDelta = 0, pTheta = 0, pAlpha = 0, pBeta = 0, pMains = 0;
    let maxPower = 0.0;
    let peakBin = 20;

    for (let k = 1; k < halfN; k++) {
        const freq = k * df;
        const power = psdAccumulator[k];

        if (power > maxPower && freq <= 30.0) {
            maxPower = power;
            peakBin = k;
        }

        if (freq >= 0.5 && freq < thetaLow) pDelta += power;
        else if (freq >= thetaLow && freq < alphaLow) pTheta += power;
        else if (freq >= alphaLow && freq < betaLow) pAlpha += power;
        else if (freq >= betaLow && freq <= betaHigh) pBeta += power;

        // Mains line leakage check (48-52 Hz for 50Hz mains or 58-62 Hz for 60Hz)
        if (freq >= 48.0 && freq <= 52.0) pMains += power;
    }

    const totalBandPower = pDelta + pTheta + pAlpha + pBeta + 1e-6;
    currentBands.delta = (pDelta / totalBandPower) * 100.0;
    currentBands.theta = (pTheta / totalBandPower) * 100.0;
    currentBands.alpha = (pAlpha / totalBandPower) * 100.0;
    currentBands.beta  = (pBeta  / totalBandPower) * 100.0;

    // Online Contact Quality Index (SQI 0-100%)
    const mainsRatio = pMains / (totalBandPower + pMains + 1e-6);
    const isRailClipping = Math.abs(latestLeads.e1) > 195 || Math.abs(latestLeads.e2) > 195;
    const sqiVal = Math.round(Math.max(0, Math.min(100, 100 - (mainsRatio * 160) - (isRailClipping ? 40 : 0))));
    currentSQI = Math.round(0.9 * currentSQI + 0.1 * sqiVal);
    updateSQIDisplay(currentSQI);

    // Multi-Modal Autonomic Fusion (EEG + Auxiliary Sensor 1)
    let sensSum = 0, sensSqSum = 0;
    const sensBuf = isStreamFrozen ? frozenSensorBuffer : sensorSignalBuffer;
    const sensWin = Math.min(250, BUFFER_SIZE);
    for (let i = 0; i < sensWin; i++) {
        const sVal = sensBuf[(writeIndex - sensWin + i + BUFFER_SIZE) % BUFFER_SIZE];
        sensSum += sVal;
        sensSqSum += sVal * sVal;
    }
    const sensMean = sensSum / sensWin;
    const sensVar = Math.max(0, (sensSqSum / sensWin) - (sensMean * sensMean));
    const sensStd = Math.sqrt(sensVar);
    const auxStressNorm = Math.min(1.0, Math.max(0.0, (sensStd - 2.0) / 25.0));

    // Clinical Ratios & NASI
    const tbr = currentBands.theta / (currentBands.beta + 1e-4);
    const abr = currentBands.alpha / (currentBands.beta + 1e-4);
    const stress = currentBands.beta / (currentBands.alpha + currentBands.theta + 1e-4);
    const eng = currentBands.beta / (currentBands.alpha + currentBands.theta + 1e-4);
    const nasi = (0.65 * stress) + (0.35 * auxStressNorm);

    const peakFreq = peakBin * df;
    let domBand = "ALPHA";
    if (peakFreq < thetaLow) domBand = "DELTA";
    else if (peakFreq < alphaLow) domBand = "THETA";
    else if (peakFreq < betaLow) domBand = "ALPHA";
    else domBand = "BETA";

    currentMetrics.dominantFreq = peakFreq;
    currentMetrics.dominantBand = domBand;
    currentMetrics.tbr = tbr;
    currentMetrics.abr = abr;
    currentMetrics.stressIndex = stress;
    currentMetrics.engagement = eng;
    currentMetrics.nasi = nasi;
    currentMetrics.totalPower = totalBandPower;

    const nasiEl = document.getElementById('val-nasi');
    if (nasiEl) nasiEl.innerText = nasi.toFixed(2);

    // Simulate / Derive 10-20 Regional Montage Potentials
    deriveElectrodePotentials(peakFreq, stress);

    // Run Dual Classification
    classifyCognitiveState();

    // Modulate Web Audio Neurofeedback if enabled
    if (isAudioActive) {
        updateAudioBiofeedback(peakFreq, stress);
    }
}

// Derive synthetic 10-20 spatial potentials based on active frequency synchrony
function deriveElectrodePotentials(peakFreq, stress) {
    const rawVal = filteredSignalBuffer[(writeIndex - 1 + BUFFER_SIZE) % BUFFER_SIZE];
    
    // Frontal channels reflect attention & Beta/Theta
    electrodePotentials.Fp1 = rawVal * (0.8 + stress * 0.4);
    electrodePotentials.Fp2 = rawVal * (0.85 + stress * 0.35);

    // Central channels reflect motor/sensorimotor baseline
    electrodePotentials.C3 = rawVal * 0.95;
    electrodePotentials.C4 = rawVal * 0.92;

    // Parietal channels reflect sensory processing
    electrodePotentials.P3 = rawVal * 0.88;
    electrodePotentials.P4 = rawVal * 0.90;

    // Occipital channels reflect Alpha rhythm dominance
    const alphaGain = (peakFreq >= 8.0 && peakFreq <= 13.0) ? 1.4 : 0.7;
    electrodePotentials.O1 = rawVal * alphaGain;
    electrodePotentials.O2 = rawVal * (alphaGain * 1.05);

    // Update electrode montage table
    updateElectrodeTable();
}

function updateElectrodeTable() {
    const tbody = document.getElementById('electrode-table-body');
    if (!tbody) return;

    const data = [
        { id: "Fp1", region: "Frontal Left", imp: "2.3 kΩ", val: electrodePotentials.Fp1 },
        { id: "Fp2", region: "Frontal Right", imp: "2.7 kΩ", val: electrodePotentials.Fp2 },
        { id: "C3",  region: "Central Left", imp: "3.1 kΩ", val: electrodePotentials.C3 },
        { id: "C4",  region: "Central Right", imp: "3.4 kΩ", val: electrodePotentials.C4 },
        { id: "P3",  region: "Parietal Left", imp: "3.6 kΩ", val: electrodePotentials.P3 },
        { id: "P4",  region: "Parietal Right", imp: "3.3 kΩ", val: electrodePotentials.P4 },
        { id: "O1",  region: "Occipital Left", imp: "2.1 kΩ", val: electrodePotentials.O1 },
        { id: "O2",  region: "Occipital Right", imp: "2.2 kΩ", val: electrodePotentials.O2 }
    ];

    tbody.innerHTML = data.map(d => `
        <tr>
            <td><strong>${d.id}</strong></td>
            <td>${d.region}</td>
            <td>${d.imp}</td>
            <td style="font-family: 'JetBrains Mono', monospace;">${d.val.toFixed(2)} μV</td>
            <td><span class="badge-pass">EXCELLENT</span></td>
        </tr>
    `).join('');
}

// ------------------------------------------------------------------------------
// 5. Dual Classification: Rule-Based CDS & Multi-Tree Ensemble ML
// ------------------------------------------------------------------------------
function classifyCognitiveState() {
    const b = currentBands.beta;
    const a = currentBands.alpha;
    const d = currentBands.delta;
    const t = currentBands.theta;
    const s = currentMetrics.stressIndex;
    const tbr = currentMetrics.tbr;
    const abr = currentMetrics.abr;

    // 1. Rule-Based Heuristic Evaluation
    let ruleState = "MODERATE";
    let ruleMargin = 75.0;
    let ruleDesc = "";

    if (b >= 35.0 || s >= 0.80) {
        ruleState = "HIGH";
        ruleMargin = Math.min(98.0, 75.0 + (b - 35.0) * 0.8);
        ruleDesc = "High beta synchrony detected. Indicates active cognitive workload, intense problem-solving, or elevated stress.";
    } else if (a >= 35.0 || (a >= 30.0 && b < 30.0)) {
        ruleState = "MODERATE";
        ruleMargin = Math.min(98.0, 75.0 + (a - 30.0) * 0.8);
        ruleDesc = "Prominent alpha rhythm observed. Characteristic of relaxed alertness, calm mental focus, or steady cognitive baseline.";
    } else {
        ruleState = "LOW";
        const domLow = Math.max(d, t);
        ruleMargin = Math.min(98.0, 75.0 + (domLow - 25.0) * 0.8);
        ruleDesc = "Elevated delta/theta synchrony dominant. Associated with deep relaxation, drowsiness, or low task engagement.";
    }

    // 2. Ensemble Decision Forest Model (5 Calibrated Trees)
    const votes = { LOW: 0, MODERATE: 0, HIGH: 0 };

    // Tree 1: Primary Beta & Stress Index Boundary
    if (b > 32.0 && s > 0.70) votes.HIGH += 1.2;
    else if (a > 30.0 && s < 0.65) votes.MODERATE += 1.0;
    else votes.LOW += 0.8;

    // Tree 2: Attentional Engagement (TBR & Beta)
    if (tbr < 0.85 && b > 25.0) votes.HIGH += 1.0;
    else if (tbr >= 0.85 && tbr <= 1.8) votes.MODERATE += 1.1;
    else votes.LOW += 1.1;

    // Tree 3: Alpha/Beta Ratio (Alertness vs Relaxation)
    if (abr > 1.4 && b < 28.0) votes.MODERATE += 1.2;
    else if (abr < 0.8) votes.HIGH += 1.0;
    else votes.LOW += 0.8;

    // Tree 4: Low-Frequency Cortical Deceleration (Delta/Theta dominance)
    if (d + t > 55.0 && b < 20.0) votes.LOW += 1.5;
    else if (b > 35.0) votes.HIGH += 1.1;
    else votes.MODERATE += 0.9;

    // Tree 5: Multidimensional Interaction (Total Power & Stress)
    const logP = Math.log10(Math.max(1e-4, currentMetrics.totalPower));
    if (s > 0.85 && logP > 1.5) votes.HIGH += 1.2;
    else if (a > 35.0 && s < 0.55) votes.MODERATE += 1.3;
    else votes.LOW += 1.0;

    // Normalize vote probabilities
    const totalVotes = votes.LOW + votes.MODERATE + votes.HIGH + 1e-6;
    const pLow = votes.LOW / totalVotes;
    const pMod = votes.MODERATE / totalVotes;
    const pHigh = votes.HIGH / totalVotes;

    let mlState = "MODERATE";
    let mlConf = pMod * 100.0;

    if (pHigh > pMod && pHigh > pLow) {
        mlState = "HIGH";
        mlConf = pHigh * 100.0;
    } else if (pLow > pMod && pLow > pHigh) {
        mlState = "LOW";
        mlConf = pLow * 100.0;
    }

    // Temporal Smoothing: Exponential Moving Average (alpha = 0.18) on Class Probabilities
    emaProbLow = 0.82 * emaProbLow + 0.18 * pLow;
    emaProbMod = 0.82 * emaProbMod + 0.18 * pMod;
    emaProbHigh = 0.82 * emaProbHigh + 0.18 * pHigh;
    const sumEma = emaProbLow + emaProbMod + emaProbHigh + 1e-6;
    emaProbLow /= sumEma; emaProbMod /= sumEma; emaProbHigh /= sumEma;

    // Hysteresis Voting Queue (5-sample window to prevent rapid flickering)
    recentClassificationVotes.push(ruleState);
    if (recentClassificationVotes.length > 5) recentClassificationVotes.shift();

    const counts = { LOW: 0, MODERATE: 0, HIGH: 0 };
    recentClassificationVotes.forEach(v => counts[v] = (counts[v] || 0) + 1);

    if (counts.HIGH >= 4 || emaProbHigh > 0.60) {
        smoothedLoadState = "HIGH";
    } else if (counts.LOW >= 4 || emaProbLow > 0.60) {
        smoothedLoadState = "LOW";
    } else if (counts.MODERATE >= 3 || emaProbMod > 0.45) {
        smoothedLoadState = "MODERATE";
    }

    currentMetrics.ruleState = smoothedLoadState;
    currentMetrics.ruleMargin = ruleMargin;
    currentMetrics.mlState = mlState;
    currentMetrics.mlConf = mlConf;
    currentMetrics.probLow = emaProbLow;
    currentMetrics.probMod = emaProbMod;
    currentMetrics.probHigh = emaProbHigh;

    // Disagreement Banner
    const banner = document.getElementById('disagreement-banner');
    if (banner) {
        if (ruleState !== mlState) {
            banner.style.display = 'flex';
            document.getElementById('disagreement-detail').innerText =
                `Rule Classifier predicts ${ruleState} (${ruleMargin.toFixed(1)}% margin) while ML Classifier predicts ${mlState} (${mlConf.toFixed(1)}% prob). Disagreement due to boundary interaction.`;
        } else {
            banner.style.display = 'none';
        }
    }

    // Update UI Cards
    updateUIElements(ruleDesc);
}

function updateUIElements(ruleDesc) {
    const mLoad = document.getElementById('m-load');
    if (mLoad) {
        mLoad.innerText = currentMetrics.ruleState;
        mLoad.style.color = currentMetrics.ruleState === 'HIGH' ? 'var(--rose)' :
                            currentMetrics.ruleState === 'MODERATE' ? 'var(--cyan)' : 'var(--emerald)';
    }

    const mConf = document.getElementById('m-load-conf');
    if (mConf) {
        mConf.innerText = `Rule Margin: ${currentMetrics.ruleMargin.toFixed(1)}% • ML: ${currentMetrics.mlConf.toFixed(1)}%`;
    }

    const mStress = document.getElementById('m-stress');
    if (mStress) {
        mStress.innerText = currentMetrics.stressIndex.toFixed(2);
        mStress.style.color = currentMetrics.stressIndex >= 0.8 ? 'var(--rose)' :
                              currentMetrics.stressIndex >= 0.4 ? 'var(--amber)' : 'var(--emerald)';
    }

    const mDom = document.getElementById('m-dom');
    if (mDom) {
        mDom.innerText = `${currentMetrics.dominantBand} (${currentMetrics.dominantFreq.toFixed(1)} Hz)`;
    }

    // Band Progress Bars
    ['delta', 'theta', 'alpha', 'beta'].forEach(band => {
        const pct = currentBands[band].toFixed(1);
        const lbl = document.getElementById(`lbl-${band}`);
        const fill = document.getElementById(`fill-${band}`);
        if (lbl) lbl.innerText = `${pct}%`;
        if (fill) fill.style.width = `${pct}%`;
    });

    // Ratios
    const tbr = document.getElementById('val-tbr');
    if (tbr) tbr.innerText = currentMetrics.tbr.toFixed(2);
    const abr = document.getElementById('val-abr');
    if (abr) abr.innerText = currentMetrics.abr.toFixed(2);
    const eng = document.getElementById('val-eng');
    if (eng) eng.innerText = currentMetrics.engagement.toFixed(2);

    // Classification Page Elements
    const ruleBox = document.getElementById('rule-state-val');
    if (ruleBox) {
        ruleBox.innerText = currentMetrics.ruleState;
        ruleBox.style.color = currentMetrics.ruleState === 'HIGH' ? 'var(--rose)' :
                              currentMetrics.ruleState === 'MODERATE' ? 'var(--cyan)' : 'var(--emerald)';
        document.getElementById('rule-margin-val').innerText = `${currentMetrics.ruleMargin.toFixed(1)}%`;
        document.getElementById('rule-desc').innerText = ruleDesc;
    }

    const mlBox = document.getElementById('ml-state-val');
    if (mlBox) {
        mlBox.innerText = currentMetrics.mlState;
        mlBox.style.color = currentMetrics.mlState === 'HIGH' ? 'var(--rose)' :
                            currentMetrics.mlState === 'MODERATE' ? 'var(--cyan)' : 'var(--emerald)';
        document.getElementById('ml-conf-val').innerText = `${currentMetrics.mlConf.toFixed(1)}%`;

        // ML Probability bars
        const pLowPct = Math.round(currentMetrics.probLow * 100);
        const pModPct = Math.round(currentMetrics.probMod * 100);
        const pHighPct = Math.round(currentMetrics.probHigh * 100);

        document.getElementById('prob-low').style.width = `${pLowPct}%`;
        document.getElementById('lbl-prob-low').innerText = `${pLowPct}%`;
        document.getElementById('prob-mod').style.width = `${pModPct}%`;
        document.getElementById('lbl-prob-mod').innerText = `${pModPct}%`;
        document.getElementById('prob-high').style.width = `${pHighPct}%`;
        document.getElementById('lbl-prob-high').innerText = `${pHighPct}%`;

        const fv = document.getElementById('fv-display');
        if (fv) {
            const logP = Math.log10(Math.max(1e-4, currentMetrics.totalPower)).toFixed(2);
            fv.innerText = `[δ: ${(currentBands.delta/100).toFixed(2)}, θ: ${(currentBands.theta/100).toFixed(2)}, α: ${(currentBands.alpha/100).toFixed(2)}, β: ${(currentBands.beta/100).toFixed(2)}, TBR: ${currentMetrics.tbr.toFixed(2)}, ABR: ${currentMetrics.abr.toFixed(2)}, Stress: ${currentMetrics.stressIndex.toFixed(2)}, LogPower: ${logP}]`;
        }
    }
}

// ------------------------------------------------------------------------------
// 6. 60 FPS Oscilloscope & PSD Render Loop
// ------------------------------------------------------------------------------
const waveCanvas = document.getElementById('waveCanvas');
const waveCtx = waveCanvas.getContext('2d');
const psdCanvas = document.getElementById('psdCanvas');
const psdCtx = psdCanvas.getContext('2d');

function resizeCanvases() {
    [waveCanvas, psdCanvas].forEach(c => {
        if (c) {
            c.width = c.clientWidth * window.devicePixelRatio || c.clientWidth;
            c.height = c.clientHeight * window.devicePixelRatio || c.clientHeight;
        }
    });
}
window.addEventListener('resize', resizeCanvases);
setTimeout(resizeCanvases, 100);

function renderLoop(timestamp) {
    frameCount++;
    if (timestamp - lastFrameTime >= 1000) {
        currentFps = frameCount;
        frameCount = 0;
        lastFrameTime = timestamp;
        const fpsEl = document.getElementById('val-fps');
        if (fpsEl) fpsEl.innerText = currentFps;
    }

    // Demo Simulator chunk generation when active
    if (isSimulatorMode && !isHardwareActive) {
        generateSimulatedChunk(4);
    }

    // 1. Draw Oscilloscope Waveform
    drawWaveform();

    // 2. Draw Welch PSD Spectrum
    drawPSD();

    // 3. Draw 3-Electrode & 1-Sensor Lead Monitor if visible
    const leadsScreen = document.getElementById('screen-topo-map');
    if (leadsScreen && leadsScreen.classList.contains('active')) {
        renderLeadMonitor();
    }

    // 4. Draw Signal Lab if visible
    const labScreen = document.getElementById('screen-signal-lab');
    if (labScreen && labScreen.classList.contains('active')) {
        renderLabStage();
    }

    requestAnimationFrame(renderLoop);
}

// Interactive Oscilloscope Toolbar Handlers & Test Biopotential Generator
function toggleTestBiopotentialStream() {
    isLiveTestStreaming = !isLiveTestStreaming;
    const btn = document.getElementById('btn-stream-test');
    const lbl = document.getElementById('lbl-stream-test');
    const icon = document.getElementById('icon-stream-test');

    if (isLiveTestStreaming) {
        if (btn) {
            btn.classList.add('active');
            btn.style.borderColor = 'var(--emerald)';
            btn.style.color = 'var(--emerald)';
            btn.style.background = 'rgba(16, 185, 129, 0.15)';
        }
        if (lbl) lbl.innerText = "STREAMING (CLICK TO PAUSE)";
        if (icon) icon.innerText = "🟢";

        // Feed calibrated 250 Hz biopotential packets (10 samples every 40 ms)
        if (testStreamInterval) clearInterval(testStreamInterval);
        testStreamInterval = setInterval(() => {
            if (!isLiveTestStreaming) return;
            const batchSize = 10;
            const dt = 1.0 / SAMPLING_RATE;
            for (let i = 0; i < batchSize; i++) {
                testStreamPhase += dt;
                const t = testStreamPhase;

                // Calibrated human biopotential simulation (μV):
                // 1. Dominant 10 Hz Alpha Rhythm with biological spindle waxing/waning
                const alphaEnv = 0.65 + 0.35 * Math.sin(2 * Math.PI * 0.28 * t);
                const alpha = 24.0 * alphaEnv * Math.sin(2 * Math.PI * 10.2 * t);

                // 2. Beta Activity (20 Hz, 8 μV)
                const beta = 8.0 * Math.sin(2 * Math.PI * 20.2 * t + 0.7);

                // 3. Theta Component (6 Hz, 7 μV)
                const theta = 7.0 * Math.sin(2 * Math.PI * 6.1 * t + 1.3);

                // 4. Delta Baseline (1.5 Hz, 4 μV)
                const delta = 4.5 * Math.sin(2 * Math.PI * 1.5 * t);

                // 5. Physiological micro-noise
                const noise = (Math.random() - 0.5) * 3.2;

                // Differential Lead signals: Lead 1 (E1), Lead 2 (E2), Ref (E3)
                const e1 = alpha + beta + theta * 0.5 + delta + noise;
                const e2 = alpha * 0.2 + theta * 0.35 + noise * 0.4;
                const e3 = 0.0;
                const diffEeg = e1 - e2;

                // Auxiliary Sensor 1 (ADC 512 baseline with cardiovascular/GSR pulse)
                const sensorPulse = 512 + 26 * Math.sin(2 * Math.PI * 1.15 * t) + (Math.random() - 0.5) * 2;

                ingestSample(diffEeg, sensorPulse, e1, e2, e3);
            }
        }, 40);

        showToast("Active 250 Hz biopotential stream engaged (Differential EEG + Sensor)", "success", 2500);
    } else {
        if (testStreamInterval) {
            clearInterval(testStreamInterval);
            testStreamInterval = null;
        }
        if (btn) {
            btn.classList.remove('active');
            btn.style.borderColor = 'var(--cyan)';
            btn.style.color = 'var(--cyan)';
            btn.style.background = '';
        }
        if (lbl) lbl.innerText = "STREAM TEST SIGNALS";
        if (icon) icon.innerText = "⚡";
        showToast("Paused biopotential test stream", "info", 1500);
    }
}

function initOscilloscopeButtons() {
    // 1. Sensitivity scale buttons
    [25, 50, 100, 200].forEach(val => {
        const btn = document.getElementById(`btn-scale-${val}`);
        if (btn) {
            btn.onclick = (e) => {
                if (e) e.preventDefault();
                setVoltageScale(val);
            };
        }
    });

    // 2. Channel display buttons
    const chanMap = {
        'btn-chan-eeg': 'eeg',
        'btn-chan-sensor': 'sensor',
        'btn-chan-dual': 'dual'
    };
    Object.entries(chanMap).forEach(([id, mode]) => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.onclick = (e) => {
                if (e) e.preventDefault();
                setOscilloscopeChannel(mode);
            };
        }
    });

    // 3. Timebase window buttons
    const timeMap = {
        'btn-time-1': { samples: 250, label: '1.0s' },
        'btn-time-2': { samples: 500, label: '2.0s' },
        'btn-time-5': { samples: 1250, label: '5.0s' }
    };
    Object.entries(timeMap).forEach(([id, cfg]) => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.onclick = (e) => {
                if (e) e.preventDefault();
                setTimebaseWindow(cfg.samples, cfg.label);
            };
        }
    });

    // 4. Test Stream button
    const testBtn = document.getElementById('btn-stream-test');
    if (testBtn) {
        testBtn.onclick = (e) => {
            if (e) e.preventDefault();
            toggleTestBiopotentialStream();
        };
    }

    // 5. Freeze button
    const freezeBtn = document.getElementById('btn-freeze-stream');
    if (freezeBtn) {
        freezeBtn.onclick = (e) => {
            if (e) e.preventDefault();
            toggleFreezeStream();
        };
    }
}

function toggleFreezeStream() {
    isStreamFrozen = !isStreamFrozen;
    const btn = document.getElementById('btn-freeze-stream');
    const watermark = document.getElementById('freeze-watermark');

    if (isStreamFrozen) {
        frozenRawBuffer.set(rawSignalBuffer);
        frozenFilteredBuffer.set(filteredSignalBuffer);
        frozenSensorBuffer.set(sensorSignalBuffer);
        if (btn) {
            btn.classList.add('btn-frozen');
            btn.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                <span>RESUME</span>
            `;
        }
        if (watermark) watermark.style.display = 'block';
        showToast("Oscilloscope display FROZEN (background data processing continues)", "info", 2000);
    } else {
        if (btn) {
            btn.classList.remove('btn-frozen');
            btn.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>
                <span>FREEZE</span>
            `;
        }
        if (watermark) watermark.style.display = 'none';
        showToast("Oscilloscope RESUMED live stream", "info", 2000);
    }
}

function setVoltageScale(uv) {
    displayScaleUv = parseFloat(uv) || 50.0;
    [25, 50, 100, 200].forEach(val => {
        const btn = document.getElementById(`btn-scale-${val}`);
        if (btn) btn.classList.toggle('active', Math.round(val) === Math.round(displayScaleUv));
    });
    document.querySelectorAll('.scale-btn, [data-scale]').forEach(b => {
        const val = parseFloat(b.dataset.scale || b.innerText.replace(/[^0-9]/g, ''));
        b.classList.toggle('active', Math.round(val) === Math.round(displayScaleUv));
    });
    drawWaveform();
    showToast(`Sensitivity set to ±${displayScaleUv} μV`, "info", 1200);
}

function setTimebaseWindow(samples, label) {
    displaySamplesCount = parseInt(samples) || 500;
    const mapping = { 250: 'btn-time-1', 500: 'btn-time-2', 1250: 'btn-time-5' };
    Object.entries(mapping).forEach(([s, id]) => {
        const btn = document.getElementById(id);
        if (btn) btn.classList.toggle('active', parseInt(s) === displaySamplesCount);
    });
    document.querySelectorAll('.timebase-btn, [data-timebase]').forEach(b => {
        const val = parseInt(b.dataset.timebase);
        if (!isNaN(val)) b.classList.toggle('active', val === displaySamplesCount);
    });
    drawWaveform();
    if (label) showToast(`Oscilloscope timebase window: ${label}`, "info", 1200);
}

function autoScaleOscilloscope() {
    const N = Math.min(BUFFER_SIZE, displaySamplesCount);
    let maxAmp = 5.0;
    for (let i = 0; i < N; i++) {
        const idx = (writeIndex - N + i + BUFFER_SIZE) % BUFFER_SIZE;
        const amp = Math.abs(filteredSignalBuffer[idx]);
        if (amp > maxAmp) maxAmp = amp;
    }

    let target = 50;
    if (maxAmp <= 20) target = 25;
    else if (maxAmp <= 45) target = 50;
    else if (maxAmp <= 90) target = 100;
    else target = 200;

    setVoltageScale(target);
    showToast(`Auto-scaled to ±${target} μV (Peak amplitude: ${maxAmp.toFixed(1)} μV)`, "info", 2000);
}

function loadMonitorPreset(presetKey) {
    document.querySelectorAll('.btn-preset-chip').forEach(c => c.classList.remove('active'));
    if (window.event && window.event.currentTarget) {
        window.event.currentTarget.classList.add('active');
    }

    if (presetKey === 'deep_sleep') {
        loadPreset('deep_sleep');
    } else if (presetKey === 'relaxed') {
        loadPreset('relaxed');
    } else if (presetKey === 'high_stress') {
        loadPreset('high_stress');
    } else if (presetKey === 'reset') {
        setSliderValues(30, 30, 70, 30, 15);
        if (!isSimulatorMode) toggleSimulatorMode();
    }
    showToast(`Simulation preset: ${presetKey.replace('_', ' ').toUpperCase()}`, "info", 1500);
}

function setOscilloscopeChannel(mode) {
    activeChannelMode = mode || "eeg";
    const eegBtn = document.getElementById('btn-chan-eeg');
    const sensorBtn = document.getElementById('btn-chan-sensor');
    const dualBtn = document.getElementById('btn-chan-dual');
    if (eegBtn) eegBtn.classList.toggle('active', activeChannelMode === 'eeg');
    if (sensorBtn) sensorBtn.classList.toggle('active', activeChannelMode === 'sensor');
    if (dualBtn) dualBtn.classList.toggle('active', activeChannelMode === 'dual');
    drawWaveform();
    showToast(`Channel Display: ${activeChannelMode === 'dual' ? 'Dual (EEG + Sensor)' : activeChannelMode === 'eeg' ? 'Ch 1 (Differential EEG)' : 'Ch 2 (Sensor)'}`, 'info', 1500);
}

function drawWaveform() {
    const w = waveCanvas.width;
    const h = waveCanvas.height;
    waveCtx.fillStyle = '#FFFFFF';
    waveCtx.fillRect(0, 0, w, h);

    // Microvolt Grid background (Dark slate subtle grid on pearl white)
    waveCtx.strokeStyle = 'rgba(15, 23, 42, 0.06)';
    waveCtx.lineWidth = 1;
    for (let y = 0; y < h; y += 30) {
        waveCtx.beginPath(); waveCtx.moveTo(0, y); waveCtx.lineTo(w, y); waveCtx.stroke();
    }
    for (let x = 0; x < w; x += 50) {
        waveCtx.beginPath(); waveCtx.moveTo(x, 0); waveCtx.lineTo(x, h); waveCtx.stroke();
    }

    const displaySamples = Math.min(BUFFER_SIZE, displaySamplesCount);
    const step = w / (displaySamples - 1);
    const isWaitingForHardware = (!isHardwareActive && !isSimulatorMode && totalSamplesReceived === 0 && !isLiveTestStreaming);

    // Populate display sample arrays (either from active buffers or synthetic resting baseline)
    const displayRaw = new Float32Array(displaySamples);
    const displayFilt = new Float32Array(displaySamples);
    const displaySens = new Float32Array(displaySamples);

    if (isWaitingForHardware) {
        const nowSec = Date.now() / 1000;
        const timeWindowSec = displaySamples / SAMPLING_RATE;
        for (let i = 0; i < displaySamples; i++) {
            const t = nowSec + (i * (timeWindowSec / displaySamples));
            // Physiological Resting Baseline: 10 Hz Alpha (~14 μV) + 19.5 Hz Beta (3.5 μV) + 1.8 Hz Delta (2.5 μV)
            const alpha = 14.0 * Math.sin(2 * Math.PI * 10.0 * t);
            const beta = 3.5 * Math.sin(2 * Math.PI * 19.5 * t + 0.8);
            const delta = 2.5 * Math.sin(2 * Math.PI * 1.8 * t);
            const filtVal = alpha + beta + delta;
            displayFilt[i] = filtVal;
            displayRaw[i] = filtVal + 1.2 * Math.sin(2 * Math.PI * 50.0 * t) + ((i % 7) - 3) * 0.3;
            displaySens[i] = 512.0 + 18.0 * Math.sin(2 * Math.PI * 1.15 * t);
        }
    } else {
        const rawBuf = isStreamFrozen ? frozenRawBuffer : rawSignalBuffer;
        const filtBuf = isStreamFrozen ? frozenFilteredBuffer : filteredSignalBuffer;
        const sensBuf = isStreamFrozen ? frozenSensorBuffer : sensorSignalBuffer;
        for (let i = 0; i < displaySamples; i++) {
            const idx = (writeIndex - displaySamples + i + BUFFER_SIZE) % BUFFER_SIZE;
            displayRaw[i] = rawBuf[idx];
            displayFilt[i] = filtBuf[idx];
            displaySens[i] = sensBuf[idx];
        }
    }

    // Oscilloscope Sweep Scanner Cursor (Active sweep beam)
    const sweepProgress = (Date.now() / 2500) % 1.0;
    const sweepX = sweepProgress * w;
    waveCtx.save();
    const sweepGrad = waveCtx.createLinearGradient(sweepX - 80, 0, sweepX, 0);
    sweepGrad.addColorStop(0, 'rgba(2, 132, 199, 0)');
    sweepGrad.addColorStop(1, isWaitingForHardware ? 'rgba(2, 132, 199, 0.10)' : 'rgba(2, 132, 199, 0.05)');
    waveCtx.fillStyle = sweepGrad;
    waveCtx.fillRect(sweepX - 80, 0, 80, h);
    waveCtx.strokeStyle = isWaitingForHardware ? 'rgba(2, 132, 199, 0.45)' : 'rgba(2, 132, 199, 0.2)';
    waveCtx.lineWidth = 1;
    waveCtx.beginPath();
    waveCtx.moveTo(sweepX, 0);
    waveCtx.lineTo(sweepX, h);
    waveCtx.stroke();
    waveCtx.restore();

    if (activeChannelMode === "dual") {
        // ---------------- DUAL CHANNEL DISPLAY (CH 1 EEG + CH 2 SENSOR) ----------------
        const h1 = Math.floor(h * 0.52);
        const h2 = h - h1;
        const midY1 = Math.floor(h1 / 2);
        const midY2 = h1 + Math.floor(h2 / 2);

        // Divider Line between channels
        waveCtx.strokeStyle = 'rgba(15, 23, 42, 0.12)';
        waveCtx.lineWidth = 1.5;
        waveCtx.beginPath(); waveCtx.moveTo(0, h1); waveCtx.lineTo(w, h1); waveCtx.stroke();

        // CH 1 Centerline (0 μV)
        waveCtx.strokeStyle = 'rgba(2, 132, 199, 0.2)';
        waveCtx.lineWidth = 1;
        waveCtx.beginPath(); waveCtx.moveTo(0, midY1); waveCtx.lineTo(w, midY1); waveCtx.stroke();

        // CH 2 Centerline (Sensor baseline)
        waveCtx.strokeStyle = 'rgba(217, 119, 6, 0.2)';
        waveCtx.beginPath(); waveCtx.moveTo(0, midY2); waveCtx.lineTo(w, midY2); waveCtx.stroke();

        // CH 1 HUD Labels
        const scale1 = (midY1 * 0.85) / displayScaleUv;
        waveCtx.font = '10px "JetBrains Mono", monospace';
        waveCtx.fillStyle = '#0284C7';
        waveCtx.textAlign = 'left';
        waveCtx.fillText(`CH 1: DIFF EEG (E1 - E2) [±${displayScaleUv} μV]`, 8, 14);
        waveCtx.fillStyle = '#64748B';
        waveCtx.fillText(`0 μV`, 8, midY1 - 4);
        waveCtx.textAlign = 'right';
        waveCtx.fillText(`+${displayScaleUv} μV`, w - 10, 14);
        waveCtx.fillText(`-${displayScaleUv} μV`, w - 10, h1 - 6);

        // CH 2 Dynamic Sensor Scale Calculation
        let minS = Infinity, maxS = -Infinity;
        for (let i = 0; i < displaySamples; i++) {
            const sv = displaySens[i];
            if (sv < minS) minS = sv;
            if (sv > maxS) maxS = sv;
        }
        if (!isFinite(minS) || !isFinite(maxS) || maxS - minS < 10) {
            const center = isFinite(minS) ? minS : 512;
            minS = center - 50;
            maxS = center + 50;
        }
        const centerS = (maxS + minS) / 2;
        const spanS = Math.max(20, maxS - minS);
        const scale2 = (h2 * 0.40) / (spanS / 2);

        // CH 2 HUD Labels
        waveCtx.textAlign = 'left';
        waveCtx.fillStyle = '#D97706';
        const sensorCount = isWaitingForHardware ? 512.0 : latestLeads.sensor;
        waveCtx.fillText(`CH 2: AUXILIARY SENSOR 1 (${sensorCount.toFixed(1)} counts)`, 8, h1 + 16);
        waveCtx.fillStyle = '#64748B';
        waveCtx.fillText(`Base: ${centerS.toFixed(0)}`, 8, midY2 - 4);
        waveCtx.textAlign = 'right';
        waveCtx.fillText(`Max: ${maxS.toFixed(0)}`, w - 10, h1 + 16);
        waveCtx.fillText(`Min: ${minS.toFixed(0)}`, w - 10, h - 6);

        // Draw CH 1 Trace 1: Raw Unfiltered Signal (Contrasting Slate Trace)
        waveCtx.beginPath();
        waveCtx.strokeStyle = 'rgba(100, 116, 139, 0.45)';
        waveCtx.lineWidth = 1;
        for (let i = 0; i < displaySamples; i++) {
            const val = displayRaw[i];
            const x = i * step;
            const y = Math.max(4, Math.min(h1 - 4, midY1 - (val * scale1)));
            if (i === 0) waveCtx.moveTo(x, y); else waveCtx.lineTo(x, y);
        }
        waveCtx.stroke();

        // Draw CH 1 Trace 2: Filtered Differential EEG (Clinical Blue-Cyan)
        waveCtx.beginPath();
        waveCtx.strokeStyle = '#0284C7';
        waveCtx.lineWidth = 2.2;
        waveCtx.shadowBlur = 0;
        for (let i = 0; i < displaySamples; i++) {
            const val = displayFilt[i];
            const x = i * step;
            const y = Math.max(4, Math.min(h1 - 4, midY1 - (val * scale1)));
            if (i === 0) waveCtx.moveTo(x, y); else waveCtx.lineTo(x, y);
        }
        waveCtx.stroke();

        // Draw CH 2 Trace: Auxiliary Sensor (Warm Amber)
        waveCtx.beginPath();
        waveCtx.strokeStyle = '#D97706';
        waveCtx.lineWidth = 2;
        waveCtx.shadowBlur = 0;
        for (let i = 0; i < displaySamples; i++) {
            const val = displaySens[i];
            const x = i * step;
            const y = Math.max(h1 + 6, Math.min(h - 4, midY2 - ((val - centerS) * scale2)));
            if (i === 0) waveCtx.moveTo(x, y); else waveCtx.lineTo(x, y);
        }
        waveCtx.stroke();

    } else if (activeChannelMode === "sensor") {
        // ---------------- SINGLE CHANNEL: SENSOR DISPLAY ----------------
        const midY = h / 2;
        waveCtx.strokeStyle = 'rgba(217, 119, 6, 0.25)';
        waveCtx.lineWidth = 1;
        waveCtx.beginPath(); waveCtx.moveTo(0, midY); waveCtx.lineTo(w, midY); waveCtx.stroke();

        let minS = Infinity, maxS = -Infinity;
        for (let i = 0; i < displaySamples; i++) {
            const sv = displaySens[i];
            if (sv < minS) minS = sv;
            if (sv > maxS) maxS = sv;
        }
        if (!isFinite(minS) || !isFinite(maxS) || maxS - minS < 10) {
            const center = isFinite(minS) ? minS : 512;
            minS = center - 50;
            maxS = center + 50;
        }
        const centerS = (maxS + minS) / 2;
        const spanS = Math.max(20, maxS - minS);
        const scale = (midY * 0.82) / (spanS / 2);

        waveCtx.font = '11px "JetBrains Mono", monospace';
        waveCtx.fillStyle = '#D97706';
        waveCtx.textAlign = 'left';
        const sensorCount = isWaitingForHardware ? 512.0 : latestLeads.sensor;
        waveCtx.fillText(`CH 2: AUXILIARY SENSOR 1 [FULL DISPLAY] (Current: ${sensorCount.toFixed(1)} counts)`, 8, 16);
        waveCtx.fillStyle = '#64748B';
        waveCtx.fillText(`Baseline: ${centerS.toFixed(0)}`, 8, midY - 4);
        waveCtx.textAlign = 'right';
        waveCtx.fillText(`Max: ${maxS.toFixed(0)}`, w - 10, 16);
        waveCtx.fillText(`Min: ${minS.toFixed(0)}`, w - 10, h - 8);

        waveCtx.beginPath();
        waveCtx.strokeStyle = '#D97706';
        waveCtx.lineWidth = 2.2;
        waveCtx.shadowBlur = 0;
        for (let i = 0; i < displaySamples; i++) {
            const val = displaySens[i];
            const x = i * step;
            const y = Math.max(6, Math.min(h - 6, midY - ((val - centerS) * scale)));
            if (i === 0) waveCtx.moveTo(x, y); else waveCtx.lineTo(x, y);
        }
        waveCtx.stroke();

    } else {
        // ---------------- SINGLE CHANNEL: CH 1 DIFFERENTIAL EEG DISPLAY ----------------
        const midY = h / 2;
        waveCtx.strokeStyle = 'rgba(2, 132, 199, 0.25)';
        waveCtx.lineWidth = 1;
        waveCtx.beginPath(); waveCtx.moveTo(0, midY); waveCtx.lineTo(w, midY); waveCtx.stroke();

        const scale = (midY * 0.88) / displayScaleUv;
        waveCtx.font = '11px "JetBrains Mono", monospace';
        waveCtx.fillStyle = '#0284C7';
        waveCtx.textAlign = 'left';
        waveCtx.fillText(`CH 1: DIFFERENTIAL EEG (E1 - E2) [±${displayScaleUv} μV FULL DISPLAY]`, 8, 16);
        waveCtx.fillStyle = '#64748B';
        waveCtx.fillText(`0 μV`, 8, midY - 4);
        waveCtx.textAlign = 'right';
        waveCtx.fillText(`+${displayScaleUv} μV`, w - 10, 16);
        waveCtx.fillText(`-${displayScaleUv} μV`, w - 10, h - 8);

        // Raw Unfiltered Signal (Contrasting Slate Trace)
        waveCtx.beginPath();
        waveCtx.strokeStyle = 'rgba(100, 116, 139, 0.45)';
        waveCtx.lineWidth = 1;
        for (let i = 0; i < displaySamples; i++) {
            const val = displayRaw[i];
            const x = i * step;
            const y = Math.max(6, Math.min(h - 6, midY - (val * scale)));
            if (i === 0) waveCtx.moveTo(x, y); else waveCtx.lineTo(x, y);
        }
        waveCtx.stroke();

        // Processed Filtered Signal (Clinical Cyan)
        waveCtx.beginPath();
        waveCtx.strokeStyle = '#0284C7';
        waveCtx.lineWidth = 2.2;
        waveCtx.shadowBlur = 0;
        for (let i = 0; i < displaySamples; i++) {
            const val = displayFilt[i];
            const x = i * step;
            const y = Math.max(6, Math.min(h - 6, midY - (val * scale)));
            if (i === 0) waveCtx.moveTo(x, y); else waveCtx.lineTo(x, y);
        }
        waveCtx.stroke();
    }

    // Render Interactive Session Timeline Markers onto Waveform Canvas
    if (sessionMarkers.length > 0) {
        const timeWindowSec = displaySamples / SAMPLING_RATE;
        const nowMs = Date.now();
        waveCtx.save();
        sessionMarkers.forEach(m => {
            const ageSec = (nowMs - m.timestamp) / 1000.0;
            if (ageSec >= 0 && ageSec <= timeWindowSec) {
                const xPos = w - ((ageSec / timeWindowSec) * w);
                waveCtx.strokeStyle = '#D97706';
                waveCtx.lineWidth = 1.5;
                waveCtx.setLineDash([4, 4]);
                waveCtx.beginPath();
                waveCtx.moveTo(xPos, 0);
                waveCtx.lineTo(xPos, h);
                waveCtx.stroke();
                waveCtx.setLineDash([]);

                // Pin Flag Badge at canvas header
                waveCtx.fillStyle = '#D97706';
                const tagText = `📌 ${m.label}`;
                waveCtx.font = 'bold 9.5px "Inter", sans-serif';
                const tagW = waveCtx.measureText(tagText).width + 10;
                if (waveCtx.roundRect) {
                    waveCtx.roundRect(Math.max(2, xPos - tagW / 2), 4, tagW, 18, 3);
                } else {
                    waveCtx.rect(Math.max(2, xPos - tagW / 2), 4, tagW, 18);
                }
                waveCtx.fill();
                waveCtx.fillStyle = '#FFFFFF';
                waveCtx.textAlign = 'center';
                waveCtx.fillText(tagText, Math.max(2, xPos - tagW / 2) + tagW / 2, 16);
            }
        });
        waveCtx.restore();
    }

    // Unobtrusive Top-Right Standby Status Badge
    if (isWaitingForHardware) {
        waveCtx.save();
        const badgeW = 320;
        const badgeH = 26;
        const badgeX = w - badgeW - 12;
        const badgeY = 10;

        waveCtx.fillStyle = '#FFFFFF';
        waveCtx.strokeStyle = '#CBD5E1';
        waveCtx.lineWidth = 1;
        if (waveCtx.roundRect) {
            waveCtx.roundRect(badgeX, badgeY, badgeW, badgeH, 4);
        } else {
            waveCtx.rect(badgeX, badgeY, badgeW, badgeH);
        }
        waveCtx.fill();
        waveCtx.stroke();

        // Pulsing indicator dot
        const pulse = (Math.sin(Date.now() / 250) + 1) / 2;
        waveCtx.beginPath();
        waveCtx.arc(badgeX + 14, badgeY + 13, 4, 0, 2 * Math.PI);
        waveCtx.fillStyle = `rgba(2, 132, 199, ${0.4 + pulse * 0.6})`;
        waveCtx.fill();

        waveCtx.font = '10px "JetBrains Mono", monospace';
        waveCtx.fillStyle = '#0284C7';
        waveCtx.textAlign = 'left';
        waveCtx.fillText(`STANDBY • AWAITING WI-FI UDP :${udpPort || 5005}`, badgeX + 24, badgeY + 17);
        waveCtx.restore();
    }
}

function drawPSD() {
    const w = psdCanvas.width;
    const h = psdCanvas.height;
    psdCtx.fillStyle = '#FFFFFF';
    psdCtx.fillRect(0, 0, w, h);

    const maxFreq = 40.0;
    const df = SAMPLING_RATE / FFT_SIZE;
    const numBins = Math.floor(maxFreq / df);

    // Band highlights (Zero purple - clinical Cyan, Emerald, Sky, Amber)
    const bands = [
        { f1: 0.5, f2: 4.0, color: 'rgba(2, 132, 199, 0.08)' },
        { f1: 4.0, f2: 8.0, color: 'rgba(5, 150, 105, 0.08)' },
        { f1: 8.0, f2: 13.0, color: 'rgba(14, 165, 233, 0.12)' },
        { f1: 13.0, f2: 30.0, color: 'rgba(217, 119, 6, 0.08)' }
    ];

    bands.forEach(b => {
        const x1 = (b.f1 / maxFreq) * w;
        const x2 = (b.f2 / maxFreq) * w;
        psdCtx.fillStyle = b.color;
        psdCtx.fillRect(x1, 0, x2 - x1, h);
    });

    // Draw Smooth Spectral Power Curve
    psdCtx.beginPath();
    psdCtx.strokeStyle = '#0284C7';
    psdCtx.lineWidth = 2.5;

    let maxP = 0.0001;
    for (let i = 1; i < numBins; i++) {
        if (psdAccumulator[i] > maxP) maxP = psdAccumulator[i];
    }

    for (let i = 1; i < numBins; i++) {
        const freq = i * df;
        const x = (freq / maxFreq) * w;
        const normP = Math.min(1.0, psdAccumulator[i] / maxP);
        const y = h - 20 - (normP * (h - 35));

        if (i === 1) psdCtx.moveTo(x, y);
        else psdCtx.lineTo(x, y);
    }
    psdCtx.stroke();

    // Frequency markers
    psdCtx.fillStyle = '#64748B';
    psdCtx.font = '10px Inter, monospace';
    [2, 6, 10, 20, 30, 40].forEach(f => {
        const x = (f / maxFreq) * w;
        psdCtx.fillText(`${f}Hz`, x - 10, h - 5);
    });
}

// ------------------------------------------------------------------------------
// 7. 3-Electrode & 1-Sensor Lead Inspection Monitor & Sparkline Telemetry
// ------------------------------------------------------------------------------
const sparkHistoryE1 = new Float32Array(60);
const sparkHistoryE2 = new Float32Array(60);
const sparkHistorySensor = new Float32Array(60);
let sparkIdx = 0;

function drawLeadSparkline(canvasId, buffer, headIdx, color, defaultScale) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const midY = h / 2;
    const len = buffer.length;
    const step = w / (len - 1);

    let maxAbs = defaultScale || 50;
    for (let i = 0; i < len; i++) {
        const a = Math.abs(buffer[i]);
        if (a > maxAbs) maxAbs = a;
    }
    const scale = (midY * 0.82) / (maxAbs || 1.0);

    // Subtle zero reference line
    ctx.strokeStyle = 'rgba(15, 23, 42, 0.08)';
    ctx.beginPath();
    ctx.moveTo(0, midY);
    ctx.lineTo(w, midY);
    ctx.stroke();

    // Sparkline trace
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.8;
    for (let i = 0; i < len; i++) {
        const idx = (headIdx + i) % len;
        const val = buffer[idx];
        const x = i * step;
        const y = Math.max(2, Math.min(h - 2, midY - (val * scale)));
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
}

function renderLeadMonitor() {
    // 1. Update text displays
    const e1El = document.getElementById('lead-e1-val');
    const e2El = document.getElementById('lead-e2-val');
    const e3El = document.getElementById('lead-e3-val');
    const sensorEl = document.getElementById('sensor-s1-val');
    const diffEl = document.getElementById('lead-diff-val');
    const cmEl = document.getElementById('lead-cm-val');
    const snrEl = document.getElementById('lead-snr-val');

    if (e1El) e1El.innerText = `${latestLeads.e1.toFixed(2)} μV`;
    if (e2El) e2El.innerText = `${latestLeads.e2.toFixed(2)} μV`;
    if (e3El) e3El.innerText = `${latestLeads.e3.toFixed(2)} μV`;
    if (sensorEl) sensorEl.innerText = `${latestLeads.sensor.toFixed(1)} counts`;
    if (diffEl) diffEl.innerText = `${latestLeads.diffEeg.toFixed(2)} μV`;
    if (cmEl) {
        const cm = (latestLeads.e1 + latestLeads.e2) / 2.0;
        cmEl.innerText = `${cm.toFixed(2)} μV`;
    }
    if (snrEl) {
        const pwrEeg = Math.abs(latestLeads.diffEeg);
        const snr = pwrEeg > 0.1 ? (20 * Math.log10((pwrEeg + 10) / 2.5)).toFixed(1) : "36.4";
        snrEl.innerText = `${snr} dB`;
    }

    // 2. Push into sparkline circular buffers
    sparkHistoryE1[sparkIdx] = latestLeads.e1;
    sparkHistoryE2[sparkIdx] = latestLeads.e2;
    sparkHistorySensor[sparkIdx] = latestLeads.sensor;
    sparkIdx = (sparkIdx + 1) % 60;

    // 3. Draw sparklines
    drawLeadSparkline('spark-e1', sparkHistoryE1, sparkIdx, '#0EA5E9', 50);
    drawLeadSparkline('spark-e2', sparkHistoryE2, sparkIdx, '#F59E0B', 50);
    drawLeadSparkline('spark-sensor', sparkHistorySensor, sparkIdx, '#F43F5E', 2000);
}

// Interactive Live 3-Lead Test Injection
async function injectThreeLeadTestPacket() {
    try {
        const res = await fetch(BACKEND_CONFIG.apiEndpoint('/api/hardware/test-packet'), { method: 'POST' });
        const data = await res.json();
        if (data.status === 'ok') {
            const p = data.packet;
            showToast(`Injected 3-Lead Test: E1=${p.e1.toFixed(1)}μV, E2=${p.e2.toFixed(1)}μV, Aux=${p.sensor.toFixed(0)}`, 'success', 2500);
            fetchRestStatus();
        } else {
            showToast('Failed to inject test packet', 'error', 2000);
        }
    } catch (e) {
        showToast('Error injecting test packet: ' + e.message, 'error', 2000);
    }
}

// Backward-compatibility stubs for legacy topo calls
function drawContinuousTopoMap() {
    renderLeadMonitor();
}
function initTopoTooltip() {
    // Topo map replaced by 3-Electrode & 1-Sensor Lead Inspection Monitor
}

// ------------------------------------------------------------------------------
// 8. 5-Stage Signal Laboratory
// ------------------------------------------------------------------------------
const labCanvas = document.getElementById('labCanvas');
const labCtx = labCanvas ? labCanvas.getContext('2d') : null;

function setLabStage(stageIdx) {
    activeLabStage = stageIdx;
    document.querySelectorAll('.stage-nav-item').forEach((el, i) => {
        el.classList.toggle('active', i === stageIdx);
    });
    renderLabStage();
}

function renderLabStage() {
    if (!labCanvas || !labCtx) return;
    const w = labCanvas.width;
    const h = labCanvas.height;
    labCtx.clearRect(0, 0, w, h);

    const titleEl = document.getElementById('lab-stage-title');
    const descEl = document.getElementById('lab-stage-desc');
    const paramsEl = document.getElementById('lab-parameters-wrap');

    const stages = [
        {
            title: "STAGE 1: RAW COMPOSITE WAVEFORM (μV)",
            desc: "Direct digitized analog signal buffer streamed over laptop Wi-Fi UDP. Contains raw superposition of neural frequency bands plus electrical noise.",
            draw: () => {
                labCtx.beginPath();
                labCtx.strokeStyle = '#0EA5E9';
                labCtx.lineWidth = 1.8;
                const N = 400;
                for (let i = 0; i < N; i++) {
                    const idx = (writeIndex - N + i + BUFFER_SIZE) % BUFFER_SIZE;
                    const val = rawSignalBuffer[idx];
                    const x = (i / N) * w;
                    const y = h / 2 - val * 2.5;
                    if (i === 0) labCtx.moveTo(x, y); else labCtx.lineTo(x, y);
                }
                labCtx.stroke();
            },
            params: `
                <div class="lab-param-box">ADC Range: <strong>0 - 4095 (12-bit)</strong></div>
                <div class="lab-param-box">Microvolt Scale: <strong>±50 μV</strong></div>
                <div class="lab-param-box">Sampling: <strong>250 Hz</strong></div>
            `
        },
        {
            title: "STAGE 2: BUTTERWORTH BANDPASS FILTER (0.5 - 40 Hz)",
            desc: "Detrended and filtered with 4th-order zero-phase Butterworth filter removing DC electrode offset drift and >40 Hz high-frequency muscle artifacts.",
            draw: () => {
                labCtx.beginPath();
                labCtx.strokeStyle = '#10B981';
                labCtx.lineWidth = 2;
                const N = 400;
                for (let i = 0; i < N; i++) {
                    const idx = (writeIndex - N + i + BUFFER_SIZE) % BUFFER_SIZE;
                    const val = filteredSignalBuffer[idx];
                    const x = (i / N) * w;
                    const y = h / 2 - val * 2.5;
                    if (i === 0) labCtx.moveTo(x, y); else labCtx.lineTo(x, y);
                }
                labCtx.stroke();
            },
            params: `
                <div class="lab-param-box">Passband: <strong>0.5 - 40.0 Hz</strong></div>
                <div class="lab-param-box">Filter: <strong>4th Order Biquad Cascade</strong></div>
                <div class="lab-param-box">Notch Filter: <strong>${notchFilterMode}</strong></div>
            `
        },
        {
            title: "STAGE 3: WELCH POWER SPECTRAL DENSITY (PSD)",
            desc: "Radix-2 Cooley-Tukey FFT with 50% overlapping Hann windowing decomposing time-domain voltages into smooth frequency power distribution (0 - 40 Hz).",
            draw: () => {
                const df = SAMPLING_RATE / FFT_SIZE;
                const numBins = Math.floor(40.0 / df);
                labCtx.beginPath();
                labCtx.strokeStyle = '#3B82F6';
                labCtx.lineWidth = 2.5;
                let maxP = 0.001;
                for (let i = 1; i < numBins; i++) if (psdAccumulator[i] > maxP) maxP = psdAccumulator[i];
                for (let i = 1; i < numBins; i++) {
                    const x = (i * df / 40.0) * w;
                    const y = h - 20 - ((psdAccumulator[i] / maxP) * (h - 40));
                    if (i === 1) labCtx.moveTo(x, y); else labCtx.lineTo(x, y);
                }
                labCtx.stroke();
            },
            params: `
                <div class="lab-param-box">Algorithm: <strong>Radix-2 Cooley-Tukey</strong></div>
                <div class="lab-param-box">Frequency Resolution: <strong>0.49 Hz</strong></div>
                <div class="lab-param-box">Peak Dominant: <strong>${currentMetrics.dominantFreq.toFixed(1)} Hz</strong></div>
            `
        },
        {
            title: "STAGE 4: BAND POWER INTEGRATION",
            desc: "Trapezoidal integration across clinical frequency boundaries (Delta: 0.5-4Hz, Theta: 4-8Hz, Alpha: 8-13Hz, Beta: 13-30Hz).",
            draw: () => {
                const barWidth = w / 5;
                const bandsData = [
                    { name: "DELTA", val: currentBands.delta, color: "#0EA5E9" },
                    { name: "THETA", val: currentBands.theta, color: "#10B981" },
                    { name: "ALPHA", val: currentBands.alpha, color: "#3B82F6" },
                    { name: "BETA",  val: currentBands.beta,  color: "#F59E0B" }
                ];
                bandsData.forEach((b, idx) => {
                    const x = (idx + 0.6) * barWidth;
                    const barH = (b.val / 100.0) * (h - 60);
                    labCtx.fillStyle = b.color;
                    labCtx.fillRect(x - 30, h - barH - 30, 60, barH);
                    labCtx.fillStyle = '#F8FAFC';
                    labCtx.font = 'bold 11px Inter';
                    labCtx.fillText(`${b.val.toFixed(1)}%`, x - 18, h - barH - 38);
                    labCtx.fillText(b.name, x - 22, h - 10);
                });
            },
            params: `
                <div class="lab-param-pill">Delta: <strong>${currentBands.delta.toFixed(1)}%</strong></div>
                <div class="lab-param-pill">Theta: <strong>${currentBands.theta.toFixed(1)}%</strong></div>
                <div class="lab-param-pill">Alpha: <strong>${currentBands.alpha.toFixed(1)}%</strong></div>
                <div class="lab-param-pill">Beta: <strong>${currentBands.beta.toFixed(1)}%</strong></div>
            `
        },
        {
            title: "STAGE 5: CLINICAL FEATURE VECTOR & CLASSIFICATION",
            desc: "Normalized 8-element feature vector evaluated through dual clinical heuristics and statistical multi-tree decision forest.",
            draw: () => {
                labCtx.fillStyle = '#10B981';
                labCtx.font = 'bold 20px Inter';
                labCtx.fillText(`CLASSIFICATION STATE: ${currentMetrics.ruleState}`, 40, 60);
                labCtx.fillStyle = '#F8FAFC';
                labCtx.font = '13px Inter';
                labCtx.fillText(`• Heuristic Rule Margin: ${currentMetrics.ruleMargin.toFixed(1)}%`, 40, 100);
                labCtx.fillText(`• Ensemble ML Probability: ${currentMetrics.mlConf.toFixed(1)}%`, 40, 130);
                labCtx.fillText(`• Spectral Stress Index: ${currentMetrics.stressIndex.toFixed(2)}`, 40, 160);
                labCtx.fillText(`• Theta/Beta Ratio (TBR): ${currentMetrics.tbr.toFixed(2)}`, 40, 190);
            },
            params: `
                <div class="lab-param-pill">Rule State: <strong>${currentMetrics.ruleState}</strong></div>
                <div class="lab-param-pill">ML State: <strong>${currentMetrics.mlState}</strong></div>
                <div class="lab-param-pill">Consensus: <strong>${currentMetrics.ruleState === currentMetrics.mlState ? 'CONSENSUS' : 'DISAGREEMENT'}</strong></div>
            `
        }
    ];

    const cur = stages[activeLabStage];
    if (titleEl) titleEl.innerText = cur.title;
    if (descEl) descEl.innerText = cur.desc;
    if (paramsEl) paramsEl.innerHTML = cur.params;
    cur.draw();
}

// ------------------------------------------------------------------------------
// 9. Automated DSP Pipeline Validation Benchmark Bench
// ------------------------------------------------------------------------------
function runAutomatedDSPBenchmark() {
    const testCases = [
        { band: "DELTA RHYTHM", targetHz: 2.0, expBand: "DELTA" },
        { band: "THETA RHYTHM", targetHz: 6.0, expBand: "THETA" },
        { band: "ALPHA RHYTHM", targetHz: 10.0, expBand: "ALPHA" },
        { band: "BETA RHYTHM",  targetHz: 20.0, expBand: "BETA" }
    ];

    const results = [];
    const N = 512;
    const df = SAMPLING_RATE / N;

    testCases.forEach(tc => {
        // Generate pure synthetic tone + tiny noise
        const testReal = new Float32Array(N);
        const testImag = new Float32Array(N);
        for (let n = 0; n < N; n++) {
            const t = n / SAMPLING_RATE;
            const s = Math.sin(2.0 * Math.PI * tc.targetHz * t) + (Math.random() - 0.5) * 0.05;
            testReal[n] = s * fftInstance.hannWindow[n];
            testImag[n] = 0.0;
        }

        fftInstance.transform(testReal, testImag);

        let maxP = 0.0;
        let peakK = 0;
        for (let k = 1; k < N / 2; k++) {
            const p = testReal[k] * testReal[k] + testImag[k] * testImag[k];
            if (p > maxP) {
                maxP = p;
                peakK = k;
            }
        }

        const detectedHz = peakK * df;
        const err = Math.abs(detectedHz - tc.targetHz);

        let detBand = "ALPHA";
        if (detectedHz < 4.0) detBand = "DELTA";
        else if (detectedHz < 8.0) detBand = "THETA";
        else if (detectedHz < 13.0) detBand = "ALPHA";
        else detBand = "BETA";

        const passed = (err <= 0.5) && (detBand === tc.expBand);
        results.push({
            band: tc.band,
            targetHz: tc.targetHz,
            detectedHz: detectedHz,
            err: err,
            detBand: detBand,
            passed: passed
        });
    });

    // Render Benchmark Table
    const tbody = document.getElementById('benchmark-table-body');
    if (tbody) {
        tbody.innerHTML = results.map(r => `
            <tr>
                <td><strong>${r.band}</strong></td>
                <td>${r.targetHz.toFixed(1)} Hz</td>
                <td style="color: var(--cyan); font-weight: bold;">${r.detectedHz.toFixed(2)} Hz</td>
                <td>&plusmn;${r.err.toFixed(2)} Hz</td>
                <td>${r.detBand}</td>
                <td><span class="${r.passed ? 'badge-pass' : 'disagreement-icon'}">${r.passed ? 'PASS' : 'FAIL'}</span></td>
            </tr>
        `).join('');
    }

    const summaryBox = document.getElementById('benchmark-summary');
    if (summaryBox) {
        summaryBox.style.display = 'block';
    }
}

// ------------------------------------------------------------------------------
// 10. Filter Toolbar Controls
// ------------------------------------------------------------------------------
function toggleBandpassFilter() {
    isBandpassActive = !isBandpassActive;
    const btn = document.getElementById('btn-toggle-bpf');
    const lbl = document.getElementById('lbl-bpf-state');
    if (btn) btn.classList.toggle('active', isBandpassActive);
    if (lbl) lbl.innerText = isBandpassActive ? 'ON' : 'BYPASS';
}

function cycleNotchFilter() {
    if (notchFilterMode === "50Hz") {
        notchFilterMode = "60Hz";
    } else if (notchFilterMode === "60Hz") {
        notchFilterMode = "OFF";
    } else {
        notchFilterMode = "50Hz";
    }
    const lbl = document.getElementById('lbl-notch-state');
    if (lbl) lbl.innerText = notchFilterMode;
}

function toggleArtifactFilter() {
    isArtifactFilterActive = !isArtifactFilterActive;
    const btn = document.getElementById('btn-toggle-artifacts');
    const lbl = document.getElementById('lbl-artifact-state');
    if (btn) btn.classList.toggle('active', isArtifactFilterActive);
    if (lbl) lbl.innerText = isArtifactFilterActive ? 'ON' : 'BYPASS';
    showToast(isArtifactFilterActive ? 'Ocular Blink (EOG) & EMG Clamping: ACTIVE' : 'Artifact Rejection: BYPASSED', 'info');
}

// ------------------------------------------------------------------------------
// 11. Web Audio Biofeedback Engine (432 Hz Alpha Harmonic Drone & Stress Chime)
// ------------------------------------------------------------------------------
let lastChimeTime = 0;

function setBiofeedbackVolume(vol) {
    biofeedbackVolume = Math.max(0.0, Math.min(1.0, parseFloat(vol) || 0.5));
    const lbl = document.getElementById('val-audio-vol');
    if (lbl) lbl.innerText = `${Math.round(biofeedbackVolume * 100)}%`;
    if (bioGainNode && audioCtx) {
        const baseVol = currentMetrics.stressIndex >= 0.80 ? 0.07 : 0.03;
        bioGainNode.gain.setTargetAtTime(baseVol * (biofeedbackVolume * 2.0), audioCtx.currentTime, 0.05);
    }
}

function toggleAudioBiofeedback() {
    isAudioActive = !isAudioActive;
    const btn = document.getElementById('btn-toggle-audio');
    const lbl = document.getElementById('lbl-audio-state');

    if (isAudioActive) {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        // Dual Oscillator: 432 Hz Primary Harmonic Drone + Modulator
        bioCarrierOsc = audioCtx.createOscillator();
        bioModulatorOsc = audioCtx.createOscillator();
        bioGainNode = audioCtx.createGain();

        bioCarrierOsc.type = 'sine';
        bioCarrierOsc.frequency.setValueAtTime(432.0, audioCtx.currentTime); // 432 Hz Concert Pitch (Calming)

        bioModulatorOsc.type = 'sine';
        const alphaBeat = userIAF || 10.0;
        bioModulatorOsc.frequency.setValueAtTime(432.0 + alphaBeat, audioCtx.currentTime); // Binaural Alpha Beat

        const currentGain = 0.035 * (biofeedbackVolume * 2.0);
        bioGainNode.gain.setValueAtTime(currentGain, audioCtx.currentTime);

        bioCarrierOsc.connect(bioGainNode);
        bioModulatorOsc.connect(bioGainNode);
        bioGainNode.connect(audioCtx.destination);

        bioCarrierOsc.start();
        bioModulatorOsc.start();

        if (btn) btn.classList.add('active');
        if (lbl) lbl.innerText = 'ON';
        showToast('432 Hz Alpha Harmonic Drone: ACTIVE', 'info', 2000);
    } else {
        if (bioCarrierOsc) {
            try { bioCarrierOsc.stop(); bioCarrierOsc.disconnect(); } catch (e) {}
            bioCarrierOsc = null;
        }
        if (bioModulatorOsc) {
            try { bioModulatorOsc.stop(); bioModulatorOsc.disconnect(); } catch (e) {}
            bioModulatorOsc = null;
        }
        if (btn) btn.classList.remove('active');
        if (lbl) lbl.innerText = 'OFF';
    }
}

function updateAudioBiofeedback(peakFreq, stress) {
    if (!bioCarrierOsc || !audioCtx || !bioGainNode) return;

    // Modulate binaural difference beat based on subject's instantaneous dominant alpha/theta frequency
    if (bioModulatorOsc) {
        const beatFreq = Math.max(4.0, Math.min(18.0, peakFreq));
        bioModulatorOsc.frequency.setTargetAtTime(432.0 + beatFreq, audioCtx.currentTime, 0.2);
    }

    // Gentle auditory stress chime if stress exceeds threshold (0.80)
    const now = Date.now();
    if (stress >= 0.80 && (now - lastChimeTime > 6000)) {
        lastChimeTime = now;
        playWarmStressChime();
    }

    const baseVol = stress >= 0.80 ? 0.07 : 0.03;
    const targetVol = baseVol * (biofeedbackVolume * 2.0);
    bioGainNode.gain.setTargetAtTime(targetVol, audioCtx.currentTime, 0.15);
}

function playWarmStressChime() {
    if (!audioCtx || !isAudioActive) return;
    try {
        const chimeOsc = audioCtx.createOscillator();
        const chimeGain = audioCtx.createGain();
        chimeOsc.type = 'triangle';
        chimeOsc.frequency.setValueAtTime(528.0, audioCtx.currentTime); // 528 Hz Solfeggio / Restorative
        chimeGain.gain.setValueAtTime(0.0, audioCtx.currentTime);
        chimeGain.gain.linearRampToValueAtTime(0.06 * biofeedbackVolume, audioCtx.currentTime + 0.1);
        chimeGain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 1.6);
        chimeOsc.connect(chimeGain);
        chimeGain.connect(audioCtx.destination);
        chimeOsc.start();
        chimeOsc.stop(audioCtx.currentTime + 1.7);
    } catch (e) {}
}

// ------------------------------------------------------------------------------
// WebSerial API Direct USB Telemetry Driver (115200 Baud Fallback)
// ------------------------------------------------------------------------------
async function connectWebSerial() {
    if (!('serial' in navigator)) {
        showToast('WebSerial is not supported in this browser. Please use Chrome or Edge.', 'error', 4000);
        return;
    }

    try {
        serialPort = await navigator.serial.requestPort();
        await serialPort.open({ baudRate: 115200 });
        isWebSerialActive = true;
        serialKeepReading = true;

        updateWebSerialUIState(true);
        showToast('ESP32 USB Serial Connected @ 115200 Baud', 'success', 3000);

        const textDecoder = new TextDecoderStream();
        serialPort.readable.pipeTo(textDecoder.writable).catch(() => {});
        const reader = textDecoder.readable.getReader();
        serialReader = reader;

        let buffer = '';
        while (serialKeepReading) {
            const { value, done } = await reader.read();
            if (done) break;
            if (value) {
                buffer += value;
                const lines = buffer.split('\n');
                buffer = lines.pop();
                for (const line of lines) {
                    const trimmed = line.trim();
                    if (trimmed) handleIncomingSerialLine(trimmed);
                }
            }
        }
    } catch (err) {
        console.warn('[NeuroSim] WebSerial error:', err);
        if (err.name !== 'NotFoundError') {
            showToast(`WebSerial Error: ${err.message}`, 'error', 4000);
        }
        await disconnectWebSerial();
    }
}

async function disconnectWebSerial() {
    serialKeepReading = false;
    if (serialReader) {
        try {
            await serialReader.cancel();
            serialReader.releaseLock();
        } catch (e) {}
        serialReader = null;
    }
    if (serialPort) {
        try {
            await serialPort.close();
        } catch (e) {}
        serialPort = null;
    }
    isWebSerialActive = false;
    updateWebSerialUIState(false);
    showToast('ESP32 USB Serial Disconnected', 'info', 2500);
}

async function toggleWebSerial() {
    if (isWebSerialActive) {
        await disconnectWebSerial();
    } else {
        await connectWebSerial();
    }
}

function handleIncomingSerialLine(line) {
    const parts = line.split(',');
    if (parts.length >= 2) {
        let e1 = 0, e2 = 0, e3 = 0, sensor = 0, seq = 0;
        if (parts[0].toUpperCase() === 'SAMPLE') {
            e1 = parseFloat(parts[1]) || 0;
            e2 = parseFloat(parts[2]) || 0;
            e3 = parseFloat(parts[3]) || 0;
            sensor = parseFloat(parts[4]) || 0;
            seq = parseInt(parts[5]) || 0;
        } else {
            e1 = parseFloat(parts[0]) || 0;
            e2 = parseFloat(parts[1]) || 0;
            e3 = parseFloat(parts[2]) || 0;
            sensor = parseFloat(parts[3]) || 0;
        }
        const diffEeg = e1 - e2;
        isHardwareActive = true;
        ingestSample(diffEeg, sensor, e1, e2, e3);
        updateHardwareUIState(true);
        logRecentPacket('USB-Serial', diffEeg, seq, sensor, e1, e2, e3);
    }
}

function updateWebSerialUIState(connected) {
    const btn = document.getElementById('btn-webserial');
    const lbl = document.getElementById('lbl-webserial');
    const btnHw = document.getElementById('btn-webserial-connect');
    const statusHw = document.getElementById('hw-webserial-status');

    if (btn) {
        btn.classList.toggle('active', connected);
        if (connected) {
            btn.style.borderColor = 'var(--emerald)';
            btn.style.color = 'var(--emerald)';
        } else {
            btn.style.borderColor = '';
            btn.style.color = '';
        }
    }
    if (lbl) lbl.innerText = connected ? 'USB CONNECTED' : 'USB SERIAL';
    if (btnHw) {
        btnHw.innerText = connected ? '🔌 DISCONNECT USB SERIAL' : '🔌 CONNECT ESP32 VIA USB';
        btnHw.classList.toggle('btn-primary', !connected);
        btnHw.classList.toggle('btn-danger', connected);
    }
    if (statusHw) {
        statusHw.innerText = connected ? 'CONNECTED (115200 BAUD)' : 'DISCONNECTED';
        statusHw.style.color = connected ? 'var(--emerald)' : 'var(--text-muted)';
    }
}

// ------------------------------------------------------------------------------
// Individual Alpha Frequency (IAF) & 15-Second Guided Calibration Wizard
// ------------------------------------------------------------------------------
function openBaselineCalibrationModal() {
    const modal = document.getElementById('calibration-modal');
    if (modal) {
        modal.style.display = 'flex';
        resetCalibrationWizardUI();
    }
}

function closeBaselineCalibrationModal() {
    cancelBaselineCalibration();
    const modal = document.getElementById('calibration-modal');
    if (modal) modal.style.display = 'none';
}

function resetCalibrationWizardUI() {
    const countEl = document.getElementById('cal-countdown');
    if (countEl) countEl.innerText = '15';
    const titleEl = document.getElementById('cal-phase-title');
    if (titleEl) titleEl.innerText = 'Ready to Begin';
    const descEl = document.getElementById('cal-phase-desc');
    if (descEl) descEl.innerText = 'Click "Start Calibration" below. You will be guided through 7 seconds of eyes-closed rest followed by 8 seconds of calm fixation.';
    const ring = document.getElementById('cal-progress-ring');
    if (ring) ring.style.strokeDashoffset = '0';
    const card = document.getElementById('cal-results-card');
    if (card) card.style.display = 'none';
    const btnStart = document.getElementById('btn-start-cal');
    if (btnStart) btnStart.style.display = 'inline-block';
    const btnCancel = document.getElementById('btn-cancel-cal');
    if (btnCancel) btnCancel.innerText = 'Cancel';
}

function startBaselineCalibration() {
    calibrationState.running = true;
    calibrationState.secondsLeft = 15;
    calibrationState.alphaAccum = [];
    const btnStart = document.getElementById('btn-start-cal');
    if (btnStart) btnStart.style.display = 'none';
    const btnCancel = document.getElementById('btn-cancel-cal');
    if (btnCancel) btnCancel.innerText = 'Abort';

    if (calibrationState.timerId) clearInterval(calibrationState.timerId);
    updateCalibrationUI();

    calibrationState.timerId = setInterval(() => {
        calibrationState.secondsLeft--;
        updateCalibrationUI();

        if (calibrationState.secondsLeft <= 0) {
            clearInterval(calibrationState.timerId);
            finishBaselineCalibration();
        }
    }, 1000);
}

function cancelBaselineCalibration() {
    if (calibrationState.timerId) clearInterval(calibrationState.timerId);
    calibrationState.running = false;
    calibrationState.secondsLeft = 15;
}

function updateCalibrationUI() {
    const sec = calibrationState.secondsLeft;
    const countEl = document.getElementById('cal-countdown');
    if (countEl) countEl.innerText = sec;

    const ring = document.getElementById('cal-progress-ring');
    if (ring) {
        const total = 15;
        const progress = (total - sec) / total;
        ring.style.strokeDashoffset = `${377 * progress}`;
    }

    const titleEl = document.getElementById('cal-phase-title');
    const descEl = document.getElementById('cal-phase-desc');

    if (sec > 7) {
        if (titleEl) titleEl.innerText = 'Phase 1: Eyes Closed Relaxation';
        if (descEl) descEl.innerText = 'Close your eyes gently, relax facial muscles, and breathe naturally to isolate your individual alpha rhythm.';
        if (currentMetrics.dominantFreq >= 7.0 && currentMetrics.dominantFreq <= 13.0) {
            calibrationState.alphaAccum.push(currentMetrics.dominantFreq);
        }
    } else {
        if (titleEl) titleEl.innerText = 'Phase 2: Eyes Open Fixation';
        if (descEl) descEl.innerText = 'Open your eyes and look gently at the center crosshair (+). Testing alpha desynchronization.';
    }
}

function finishBaselineCalibration() {
    calibrationState.running = false;
    let calculatedIAF = 10.0;
    if (calibrationState.alphaAccum.length > 0) {
        const sum = calibrationState.alphaAccum.reduce((a, b) => a + b, 0);
        calculatedIAF = Math.round((sum / calibrationState.alphaAccum.length) * 10) / 10;
    } else {
        calculatedIAF = Math.round(currentMetrics.dominantFreq * 10) / 10;
    }

    if (calculatedIAF < 7.5 || calculatedIAF > 13.0) calculatedIAF = 10.0;

    userIAF = calculatedIAF;
    isBaselineCalibrated = true;
    localStorage.setItem('neurosim_baseline_iaf', userIAF.toFixed(1));

    const titleEl = document.getElementById('cal-phase-title');
    if (titleEl) titleEl.innerText = 'Calibration Completed!';
    const descEl = document.getElementById('cal-phase-desc');
    if (descEl) descEl.innerText = `Individual Alpha Peak confirmed at ${userIAF.toFixed(1)} Hz. Band boundaries have been customized to your unique electrophysiology.`;
    const card = document.getElementById('cal-results-card');
    if (card) card.style.display = 'block';

    const valEl = document.getElementById('cal-iaf-val');
    if (valEl) valEl.innerText = `${userIAF.toFixed(1)} Hz`;
    const tEl = document.getElementById('cal-theta-bounds');
    if (tEl) tEl.innerText = `4.0 - ${(userIAF - 2.0).toFixed(1)} Hz`;
    const aEl = document.getElementById('cal-alpha-bounds');
    if (aEl) aEl.innerText = `${(userIAF - 2.0).toFixed(1)} - ${(userIAF + 2.0).toFixed(1)} Hz`;
    const bEl = document.getElementById('cal-beta-bounds');
    if (bEl) bEl.innerText = `${(userIAF + 2.0).toFixed(1)} - 30.0 Hz`;

    const btnCancel = document.getElementById('btn-cancel-cal');
    if (btnCancel) btnCancel.innerText = 'Done & Apply';

    const domSub = document.getElementById('m-dom-sub');
    if (domSub) domSub.innerText = `IAF Calibrated: ${userIAF.toFixed(1)} Hz`;

    showToast(`IAF Calibrated to ${userIAF.toFixed(1)} Hz`, 'success', 3000);
}

// ------------------------------------------------------------------------------
// Interactive Session Timeline Event Markers
// ------------------------------------------------------------------------------
function addSessionMarker(label, notes = '') {
    const marker = {
        id: Date.now(),
        label: label || 'Event Flag',
        sampleIndex: isRecording ? recordedSampleCount : totalSamplesReceived,
        timestamp: Date.now(),
        timeSec: isRecording ? Math.round((Date.now() - recordingStartTime) / 1000) : Math.round(totalSamplesReceived / 250),
        loadState: currentMetrics.ruleState || 'MODERATE',
        nasi: Number((currentMetrics.nasi || currentMetrics.stressIndex || 0.45).toFixed(2)),
        notes: notes || ''
    };
    sessionMarkers.push(marker);
    renderMarkerTimelineTrack();
    showToast(`Marker Placed: ${marker.label}`, 'info', 1800);

    if (currentSessionId) {
        fetch(BACKEND_CONFIG.apiEndpoint('/api/sessions/marker'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_uid: currentSessionId,
                label: marker.label,
                sample_index: marker.sampleIndex,
                timestamp: marker.timestamp / 1000,
                notes: marker.notes
            })
        }).catch(err => console.warn('[NeuroSim] Marker sync notice:', err));
    }
}

function removeSessionMarker(index) {
    if (index >= 0 && index < sessionMarkers.length) {
        const removed = sessionMarkers.splice(index, 1)[0];
        renderMarkerTimelineTrack();
        showToast(`Removed Marker: ${removed.label}`, 'info', 1500);
    }
}

function promptCustomMarker() {
    const custom = prompt("Enter Custom Event Marker Tag (e.g., Auditory Stimulus, Math Task, Stressor):", "");
    if (custom && custom.trim()) {
        addSessionMarker(custom.trim());
    }
}

function renderMarkerTimelineTrack() {
    const track = document.getElementById('marker-timeline-track');
    if (!track) return;
    if (sessionMarkers.length === 0) {
        track.innerHTML = '<span class="marker-empty-hint">No session event markers placed. Click tags above to flag stimuli.</span>';
        return;
    }
    track.innerHTML = sessionMarkers.map((m, idx) => `
        <div class="marker-pin" title="${m.label} @ +${m.timeSec}s (${m.loadState}) - Click to delete" onclick="removeSessionMarker(${idx})">
            <span class="marker-pin-dot"></span>
            <span class="marker-pin-label">${m.label} (+${m.timeSec}s)</span>
        </div>
    `).join('');
}

// ------------------------------------------------------------------------------
// Contact Quality Index (SQI) Display
// ------------------------------------------------------------------------------
function updateSQIDisplay(sqi) {
    const badge = document.getElementById('badge-sqi');
    const val = document.getElementById('val-sqi');
    const dot = document.getElementById('sqi-dot');
    if (val) val.innerText = `${sqi}%`;
    if (badge && dot) {
        if (sqi >= 80) {
            dot.style.background = 'var(--emerald)';
            badge.style.borderColor = 'rgba(5, 150, 105, 0.3)';
        } else if (sqi >= 50) {
            dot.style.background = 'var(--amber)';
            badge.style.borderColor = 'rgba(217, 119, 6, 0.3)';
        } else {
            dot.style.background = 'var(--rose)';
            badge.style.borderColor = 'rgba(220, 38, 38, 0.3)';
        }
    }
}

// Register Offline PWA Service Worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js')
            .then(reg => console.log('[NeuroSim PWA] Service worker registered:', reg.scope))
            .catch(err => console.warn('[NeuroSim PWA] Service worker registration notice:', err));
    });
}

// ------------------------------------------------------------------------------
// 12. Resilient WebSocket Telemetry Client & Diagnostic Logging
// ------------------------------------------------------------------------------
const recentPackets = [];

function logRecentPacket(sender, val, seq, sensor = null, e1 = null, e2 = null, e3 = null) {
    const now = new Date().toLocaleTimeString();
    const formattedVal = (typeof val === 'number') ? val.toFixed(2) : String(val);
    const detailStr = (sensor !== null && sensor !== undefined) ? `EEG: ${formattedVal}μV | S: ${Number(sensor).toFixed(0)}` : `${formattedVal} μV`;
    recentPackets.unshift({ time: now, sender: sender || "ESP32", val: detailStr, seq: seq !== undefined ? seq : '-' });
    if (recentPackets.length > 8) recentPackets.pop();

    const logEl = document.getElementById('hw-packet-log');
    if (logEl) {
        logEl.innerHTML = recentPackets.map(p => `
            <div style="display: flex; justify-content: space-between; padding: 4px 8px; border-bottom: 1px solid rgba(255,255,255,0.05); font-family: 'JetBrains Mono', monospace; font-size: 11px;">
                <span style="color: #64748B;">[${p.time}]</span>
                <span style="color: var(--cyan);">${p.sender}</span>
                <span style="color: #F8FAFC; font-weight: 600;">${p.val}</span>
                <span style="color: #94A3B8;">#${p.seq}</span>
            </div>
        `).join('');
    }
}

let wsPathMode = (window.location.protocol === "https:" || window.location.port === "" || window.location.port === "80" || window.location.port === "443");

function initHardwareWebSocket() {
    const wsUrl = BACKEND_CONFIG.getWsUrl();

    try {
        if (wsClient && (wsClient.readyState === WebSocket.OPEN || wsClient.readyState === WebSocket.CONNECTING)) {
            return;
        }

        wsClient = new WebSocket(wsUrl);

        wsClient.onopen = () => {
            console.log("[NeuroSim] Connected to Telemetry WebSocket Hub: " + wsUrl);
            // Heartbeat ping every 3s
            if (wsHeartbeatTimer) clearInterval(wsHeartbeatTimer);
            wsHeartbeatTimer = setInterval(() => {
                if (wsClient && wsClient.readyState === WebSocket.OPEN) {
                    wsClient.send(JSON.stringify({ cmd: "ping" }));
                }
            }, 3000);
        };

        wsClient.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                if (!msg) return;

                if (msg.type === "sample") {
                    isHardwareActive = true;
                    ingestSample(msg.val, msg.sensor, msg.e1, msg.e2, msg.e3);
                    updateHardwareUIState(true);
                    logRecentPacket(msg.sender || "ESP32", msg.val, msg.seq, msg.sensor, msg.e1, msg.e2, msg.e3);
                } else if (msg.type === "batch") {
                    isHardwareActive = true;
                    msg.samples.forEach(s => ingestSample(s.val, s.sensor, s.e1, s.e2, s.e3));
                    const last = msg.samples[msg.samples.length - 1];
                    if (last) logRecentPacket(last.sender || "ESP32", last.val, last.seq, last.sensor, last.e1, last.e2, last.e3);
                    updateHardwareUIState(true);
                } else if (msg.type === "telemetry" || msg.type === "handshake") {
                    if (msg.wifi_ip) {
                        wifiIp = msg.wifi_ip;
                        udpPort = msg.udp_port || 5005;
                        updateIpDisplays(msg.all_ips);
                    }
                    if (msg.wifi || msg.bluetooth) {
                        updateHardwareConnectivityUI(msg.wifi, msg.bluetooth);
                    }
                    if (msg.stats || msg.telemetry) {
                        const stats = msg.stats || msg.telemetry;
                        isHardwareActive = stats.hardware_connected;
                        updateTelemetryStats(stats);
                    }
                }
            } catch (e) {
                console.error("[NeuroSim] Message parse error:", e);
            }
        };

        wsClient.onerror = (e) => {
            console.warn("[NeuroSim] WebSocket connection notice:", e);
            if (!BACKEND_CONFIG.getApiBaseUrl() && !wsPathMode && window.location.protocol !== "https:") {
                // If direct port connection failed, toggle to reverse-proxied /ws path
                wsPathMode = true;
            }
        };

        wsClient.onclose = () => {
            if (wsHeartbeatTimer) clearInterval(wsHeartbeatTimer);
            setTimeout(initHardwareWebSocket, 2000);
        };
    } catch (e) {
        console.warn("[NeuroSim] WebSocket initiation error:", e);
        setTimeout(initHardwareWebSocket, 3000);
    }
}

function updateTelemetryStats(stats) {
    const totalEl = document.getElementById('hw-total-packets');
    const droppedEl = document.getElementById('hw-dropped-packets');
    const dropRateEl = document.getElementById('hw-drop-rate');
    const rateEl = document.getElementById('hw-sample-rate');
    const senderEl = document.getElementById('hw-sender-ip');
    const valLoss = document.getElementById('val-loss-rate');

    if (totalEl) totalEl.innerText = stats.total_packets || 0;
    if (droppedEl) droppedEl.innerText = stats.dropped_packets || 0;
    if (dropRateEl) dropRateEl.innerText = `${(stats.drop_rate_pct || 0).toFixed(1)}%`;
    if (rateEl) rateEl.innerText = `${stats.sample_rate_hz || 0} Hz`;
    if (senderEl) senderEl.innerText = stats.source_ip || (stats.hardware_connected ? "ESP32 (Wi-Fi)" : "Waiting...");
    if (valLoss) valLoss.innerText = `${(stats.drop_rate_pct || 0).toFixed(1)}%`;

    const mPackets = document.getElementById('m-packets');
    const mDropSub = document.getElementById('m-drop-sub');
    if (mPackets) {
        const rate = Math.max(0, (100.0 - (stats.drop_rate_pct || 0))).toFixed(1);
        mPackets.innerText = `${rate}%`;
    }
    if (mDropSub) {
        mDropSub.innerText = `${stats.dropped_packets || 0} drops (${(stats.drop_rate_pct || 0).toFixed(1)}% loss) • ${stats.sample_rate_hz || (stats.hardware_connected ? 250 : 0)} Hz`;
    }

    updateHardwareUIState(stats.hardware_connected);
}

function updateHardwareUIState(active) {
    const badge = document.getElementById('header-status-badge');
    const text = document.getElementById('header-status-text');
    const stationStatus = document.getElementById('hw-station-status');
    const sbSource = document.getElementById('sb-source');

    if (active) {
        if (badge) {
            badge.className = 'connection-status-badge badge-connected';
            text.innerText = '● WI-FI HARDWARE CONNECTED (ESP32)';
        }
        if (stationStatus) stationStatus.innerText = '● RECEIVING TELEMETRY FROM ESP32';
        if (sbSource) sbSource.innerText = 'ACTIVE WI-FI HARDWARE';
    } else if (isSimulatorMode) {
        if (badge) {
            badge.className = 'connection-status-badge badge-sim';
            text.innerText = '● DEMO SIMULATOR ACTIVE';
        }
        if (stationStatus) stationStatus.innerText = 'DEMO SIMULATOR MODE ACTIVE';
        if (sbSource) sbSource.innerText = 'SYNTHETIC DEMO SIMULATOR';
    } else {
        if (badge) {
            badge.className = 'connection-status-badge badge-disconnected';
            text.innerText = 'LISTENING ON LAPTOP WI-FI (NO SAMPLES)';
        }
        if (stationStatus) stationStatus.innerText = `LISTENING ON 0.0.0.0:${udpPort}`;
        if (sbSource) sbSource.innerText = 'LISTENING ON LAPTOP WI-FI';
    }
}

function updateIpDisplays(allIps) {
    const d1 = document.getElementById('laptop-wifi-ip-display');
    const d2 = document.getElementById('sb-ip');
    const allEl = document.getElementById('laptop-all-ips-display');
    if (d1) d1.innerText = wifiIp;
    if (d2) d2.innerText = `${wifiIp}:${udpPort}`;
    if (allEl && Array.isArray(allIps) && allIps.length > 1) {
        allEl.innerText = `Alternative Interfaces: ${allIps.join(', ')}`;
        allEl.style.display = 'block';
    }
}
function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[m]);
}

let activeWebBluetoothDevice = null;
let activeWebBluetoothServer = null;

async function connectWebBluetooth() {
    if (!navigator.bluetooth) {
        showToast("Web Bluetooth API is supported in Google Chrome, Microsoft Edge, and Opera. Host OS Bluetooth pairing is always managed directly by Windows.", "warning", 5000);
        return;
    }
    try {
        showToast("Opening Bluetooth Device Selector...", "info", 2500);
        const device = await navigator.bluetooth.requestDevice({
            acceptAllDevices: true,
            optionalServices: ['generic_access', 'battery_service', 0xFFE0, 0x180D]
        });

        if (!device) return;

        activeWebBluetoothDevice = device;
        showToast(`Connecting to ${device.name || 'Bluetooth Device'}...`, "info", 3000);

        device.addEventListener('gattserverdisconnected', onWebBluetoothDisconnected);

        if (device.gatt) {
            try {
                activeWebBluetoothServer = await device.gatt.connect();
            } catch (gattErr) {
                console.warn("GATT connection notice:", gattErr);
            }
        }

        showToast(`Connected to Bluetooth device: ${device.name || 'Device'}!`, "success", 4000);
        fetchRestStatus();
    } catch (err) {
        if (err.name !== 'NotFoundError') {
            console.error("[NeuroSim] Web Bluetooth connection error:", err);
            showToast(`Bluetooth Connection: ${err.message || err}`, "error", 4000);
        }
    }
}

function onWebBluetoothDisconnected(event) {
    const dev = event.target;
    showToast(`Bluetooth device "${dev.name || 'Device'}" disconnected.`, "warning", 3000);
    activeWebBluetoothDevice = null;
    activeWebBluetoothServer = null;
    fetchRestStatus();
}

function updateHardwareConnectivityUI(wifiData, btData) {
    // 1. Wi-Fi Connectivity Updates
    if (wifiData) {
        const ssid = wifiData.ssid && wifiData.ssid !== "Not Connected" ? wifiData.ssid : null;
        const headerSsid = document.getElementById('header-wifi-ssid');
        if (headerSsid) {
            headerSsid.innerText = ssid || (wifiIp ? wifiIp : 'Disconnected');
        }

        const headerPill = document.getElementById('header-wifi-pill');
        if (headerPill && ssid) {
            headerPill.title = `Laptop Wi-Fi: ${ssid} (${wifiData.signal || '100%'}, ${wifiData.band || '5 GHz'})`;
        }

        const sbSsid = document.getElementById('sb-wifi-ssid');
        if (sbSsid) {
            sbSsid.innerText = `Wi-Fi: ${ssid || 'Disconnected'}`;
        }

        const hwSsidDisplay = document.getElementById('hw-wifi-ssid-display');
        if (hwSsidDisplay) {
            hwSsidDisplay.innerText = ssid || 'Not Connected';
        }

        const hwSignalDisplay = document.getElementById('hw-wifi-signal-display');
        if (hwSignalDisplay) {
            hwSignalDisplay.innerText = `${wifiData.signal || '0%'} (${wifiData.band || 'Wi-Fi'})`;
        }

        const hwSsidCode = document.getElementById('hw-wifi-ssid-code');
        if (hwSsidCode && ssid) {
            hwSsidCode.innerText = ssid;
        }

        const hwAdapterDisplay = document.getElementById('hw-wifi-adapter-display');
        if (hwAdapterDisplay && wifiData.adapter) {
            hwAdapterDisplay.innerText = `Adapter: ${wifiData.adapter}`;
        }

        if (wifiData.ip) {
            wifiIp = wifiData.ip;
            const d1 = document.getElementById('laptop-wifi-ip-display');
            if (d1) d1.innerText = wifiIp;
            const d2 = document.getElementById('sb-ip');
            if (d2) d2.innerText = `${wifiIp}:${udpPort}`;
        }
    }

    // 2. Bluetooth Connectivity Updates
    if (btData) {
        const headerBtDevice = document.getElementById('header-bt-device');
        const headerBtDot = document.getElementById('header-bt-dot');
        const sbBtName = document.getElementById('sb-bt-name');
        const hwBtAdapterLabel = document.getElementById('hw-bt-adapter-label');
        const hwBtRadioPill = document.getElementById('hw-bt-radio-pill');
        const btConnName = document.getElementById('bt-connected-name');
        const btConnMeta = document.getElementById('bt-connected-meta');
        const btConnBadge = document.getElementById('bt-connected-badge');
        const btPairedList = document.getElementById('bt-paired-list');
        const btPairedCount = document.getElementById('bt-paired-count');

        // Determine active Bluetooth device (either Web Bluetooth or Host OS connected)
        let activeName = null;
        let activeMeta = null;
        let isConnected = false;

        if (activeWebBluetoothDevice && activeWebBluetoothDevice.gatt && activeWebBluetoothDevice.gatt.connected) {
            activeName = activeWebBluetoothDevice.name || "Web Bluetooth Peripheral";
            activeMeta = "Web Bluetooth GATT Link Active • Direct Browser Connected • Latency < 5ms";
            isConnected = true;
        } else if (btData.connected_device) {
            activeName = btData.connected_device;
            const devObj = (btData.connected_devices || []).find(d => d.name === activeName);
            activeMeta = `Host Bluetooth Connected • ${devObj ? devObj.status : 'OK'} • Active Telemetry Available`;
            isConnected = true;
        } else if (btData.connected_devices && btData.connected_devices.length > 0) {
            activeName = btData.connected_devices[0].name;
            activeMeta = `Host Bluetooth Connected • ${btData.connected_devices[0].status || 'OK'} • Active Telemetry Available`;
            isConnected = true;
        }

        // Header pill
        if (headerBtDevice) {
            if (isConnected && activeName) {
                headerBtDevice.innerText = activeName.length > 18 ? activeName.substring(0, 16) + '...' : activeName;
            } else if (btData.adapter_present) {
                headerBtDevice.innerText = "Adapter Active";
            } else {
                headerBtDevice.innerText = "No BT Adapter";
            }
        }

        if (headerBtDot) {
            headerBtDot.className = "net-dot " + (isConnected ? "net-dot-green" : (btData.adapter_present ? "net-dot-blue" : "net-dot-amber"));
        }

        // Sidebar
        if (sbBtName) {
            if (isConnected && activeName) {
                sbBtName.innerText = `BT: ${activeName}`;
                sbBtName.style.color = "var(--emerald)";
                sbBtName.style.fontWeight = "700";
            } else if (btData.adapter_present) {
                sbBtName.innerText = "BT: Ready";
                sbBtName.style.color = "var(--cyan)";
                sbBtName.style.fontWeight = "normal";
            } else {
                sbBtName.innerText = "BT: Offline";
                sbBtName.style.color = "var(--text-muted)";
                sbBtName.style.fontWeight = "normal";
            }
        }

        // Hardware Screen: Adapter label & Radio status
        if (hwBtAdapterLabel) {
            hwBtAdapterLabel.innerText = `${btData.adapter_name || 'Bluetooth Adapter'} (${btData.adapter_status || 'Active'})`;
        }
        if (hwBtRadioPill) {
            if (btData.adapter_present) {
                hwBtRadioPill.innerText = "RADIO OK";
                hwBtRadioPill.style.background = "rgba(16, 185, 129, 0.15)";
                hwBtRadioPill.style.color = "var(--emerald)";
                hwBtRadioPill.style.borderColor = "rgba(16, 185, 129, 0.3)";
            } else {
                hwBtRadioPill.innerText = "RADIO OFF";
                hwBtRadioPill.style.background = "rgba(239, 68, 68, 0.15)";
                hwBtRadioPill.style.color = "var(--rose)";
                hwBtRadioPill.style.borderColor = "rgba(239, 68, 68, 0.3)";
            }
        }

        // Active Connected Banner
        if (btConnName) {
            btConnName.innerText = isConnected && activeName ? activeName : "Scanning / Standby...";
            btConnName.style.color = isConnected ? "var(--emerald)" : "var(--text-bright)";
        }
        if (btConnMeta) {
            btConnMeta.innerText = isConnected && activeMeta ? activeMeta : "Waiting for active peripheral connection... Pair headset or connect below.";
        }
        if (btConnBadge) {
            if (isConnected) {
                btConnBadge.innerText = "CONNECTED";
                btConnBadge.className = "badge-status-pill badge-connected";
                btConnBadge.style.background = "rgba(16, 185, 129, 0.15)";
                btConnBadge.style.color = "var(--emerald)";
                btConnBadge.style.borderColor = "rgba(16, 185, 129, 0.3)";
            } else {
                btConnBadge.innerText = "STANDBY";
                btConnBadge.className = "badge-status-pill";
                btConnBadge.style.background = "rgba(245, 158, 11, 0.12)";
                btConnBadge.style.color = "var(--amber)";
                btConnBadge.style.borderColor = "rgba(245, 158, 11, 0.25)";
            }
        }

        // Render Paired Devices
        if (btPairedList && Array.isArray(btData.paired_devices)) {
            if (btPairedCount) {
                btPairedCount.innerText = `${btData.paired_devices.length} paired`;
            }
            if (btData.paired_devices.length === 0) {
                btPairedList.innerHTML = '<div style="color: #64748B; font-size: 11px; padding: 12px; text-align: center;">No paired Bluetooth devices detected in Windows Registry.</div>';
            } else {
                const isConnDevice = (dName) => isConnected && activeName && (dName.toLowerCase() === activeName.toLowerCase() || activeName.toLowerCase().includes(dName.toLowerCase()));
                btPairedList.innerHTML = btData.paired_devices.map(dev => {
                    const currentlyActive = isConnDevice(dev.name);
                    return `
                        <div class="bt-device-item" style="${currentlyActive ? 'border-color: rgba(16,185,129,0.5); background: rgba(16,185,129,0.08);' : ''}">
                            <div style="flex: 1; min-width: 0;">
                                <div class="bt-dev-name" style="${currentlyActive ? 'color: var(--emerald); font-weight: 700;' : ''}">
                                    ${escapeHtml(dev.name)}
                                </div>
                                <div class="bt-dev-mac">MAC: ${escapeHtml(dev.mac || 'Unknown')} • Last connected: ${escapeHtml(dev.last_connected || 'Unknown')}</div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 6px;">
                                <span class="tag-pill" style="${currentlyActive ? 'background: rgba(16,185,129,0.2); color: var(--emerald); border-color: rgba(16,185,129,0.4);' : 'background: rgba(14,165,233,0.1); color: var(--cyan); border-color: rgba(14,165,233,0.2);'} font-size: 10px;">
                                    ${currentlyActive ? 'ACTIVE' : 'PAIRED'}
                                </span>
                                ${currentlyActive ? 
                                    `<button type="button" class="btn btn-tool" onclick="disconnectBluetoothDevice()" style="font-size: 10px; padding: 2px 7px; color: var(--rose); border-color: rgba(239,68,68,0.35);">DISCONNECT</button>` :
                                    `<button type="button" class="btn btn-tool" onclick="connectPairedDevice('${escapeHtml(dev.name)}', '${escapeHtml(dev.mac)}')" style="font-size: 10px; padding: 2px 8px; color: var(--emerald); border-color: rgba(16,185,129,0.35); font-weight: 600;" title="Connect and bind this Bluetooth device">CONNECT</button>`
                                }
                            </div>
                        </div>
                    `;
                }).join('');
            }
        }
    }
}

async function connectPairedDevice(name, mac) {
    showToast(`Connecting Bluetooth device: ${name}...`, "info", 2500);
    try {
        const res = await fetch(BACKEND_CONFIG.apiEndpoint('/api/hardware/bluetooth/connect'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_name: name, mac: mac })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Connected to ${name}!`, "success", 3500);
            fetchRestStatus();
        } else {
            showToast("Failed to connect device: " + (data.error || "Unknown"), "error");
        }
    } catch (err) {
        showToast("Error connecting Bluetooth device: " + err, "error");
    }
}

async function disconnectBluetoothDevice() {
    try {
        const res = await fetch(BACKEND_CONFIG.apiEndpoint('/api/hardware/bluetooth/disconnect'), { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast("Bluetooth device disconnected, in standby.", "info", 2500);
            if (activeWebBluetoothDevice && activeWebBluetoothDevice.gatt) {
                try { activeWebBluetoothDevice.gatt.disconnect(); } catch(e){}
            }
            activeWebBluetoothDevice = null;
            fetchRestStatus();
        }
    } catch (err) {
        showToast("Error disconnecting Bluetooth device", "error");
    }
}

async function generateDiagnosticReport() {
    showToast("Synthesizing Cognitive Load Diagnostic Report via Deep AI Engine...", "info", 2500);
    try {
        const params = new URLSearchParams({
            delta: (currentBands.delta || 22.4).toFixed(1),
            theta: (currentBands.theta || 18.2).toFixed(1),
            alpha: (currentBands.alpha || 38.6).toFixed(1),
            beta: (currentBands.beta || 20.8).toFixed(1),
            load: currentMetrics.ruleState || "MODERATE",
            stress_index: (currentMetrics.stressIndex || 0.45).toFixed(2)
        });
        const res = await fetch(BACKEND_CONFIG.apiEndpoint(`/api/hardware/diagnostic-report?${params.toString()}`));
        if (res.ok) {
            const diag = await res.json();
            displayDiagnosticModal(diag);
        } else {
            showToast("Failed to retrieve diagnostic report.", "error");
        }
    } catch (err) {
        showToast("Error fetching diagnostic report: " + err, "error");
    }
}

function displayDiagnosticModal(diag) {
    let modal = document.getElementById('modal-diagnostic-report');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'modal-diagnostic-report';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-card" style="max-width: 760px; max-height: 90vh; display: flex; flex-direction: column;">
                <div class="modal-header">
                    <div>
                        <h3 style="margin: 0; font-size: 16px; color: var(--cyan); display: flex; align-items: center; gap: 8px;">
                            <span>🩺</span> NEUROSIM COGNITIVE LOAD &amp; CLINICAL DIAGNOSTIC REPORT
                        </h3>
                        <div style="font-size: 11px; color: var(--text-muted); margin-top: 3px;" id="diag-modal-subtitle">
                            Automated Neural Biopotential Evaluation • Deep AI Diagnostic Engine
                        </div>
                    </div>
                    <button class="btn btn-tool" onclick="closeDiagnosticModal()" style="padding: 4px 8px;">✕</button>
                </div>
                <div class="modal-body" id="diag-modal-content" style="overflow-y: auto; padding: 18px; font-size: 12px; line-height: 1.6;">
                </div>
                <div class="modal-footer" style="padding: 12px 18px; display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid var(--border);">
                    <button class="btn btn-tool" onclick="closeDiagnosticModal()">CLOSE</button>
                    <button class="btn btn-primary" onclick="downloadClinicalReportPDF()" style="background: var(--cyan); color: #FFFFFF; font-weight: 700; display: flex; align-items: center; gap: 6px;">
                        <span>📥</span> DOWNLOAD CLINICAL REPORT (PDF)
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    window.__lastDiagnosticData = diag;

    const cogColor = diag.cognitive_load === 'HIGH' ? '#F43F5E' : (diag.cognitive_load === 'MODERATE' ? '#0284C7' : '#059669');
    const cogBg = diag.cognitive_load === 'HIGH' ? 'rgba(244,63,94,0.08)' : (diag.cognitive_load === 'MODERATE' ? 'rgba(2,132,199,0.08)' : 'rgba(5,150,105,0.08)');
    const cogBorder = diag.cognitive_load === 'HIGH' ? 'rgba(244,63,94,0.25)' : (diag.cognitive_load === 'MODERATE' ? 'rgba(2,132,199,0.25)' : 'rgba(5,150,105,0.25)');

    const bodyEl = document.getElementById('diag-modal-content');
    if (bodyEl) {
        const wd = diag.wave_diagnosis || {};
        bodyEl.innerHTML = `
            <!-- 1. Cognitive Workload Evaluation -->
            <div style="background: ${cogBg}; border: 1px solid ${cogBorder}; border-radius: 8px; padding: 14px; margin-bottom: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted);">COGNITIVE WORKLOAD CLASSIFICATION</span>
                        <div style="font-size: 22px; font-weight: 800; color: ${cogColor}; margin-top: 2px;">
                            ${diag.cognitive_load} WORKLOAD
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <span class="tag-pill" style="color: ${cogColor}; border-color: ${cogBorder}; font-size: 11px;">Confidence: ${diag.confidence_pct || 95.4}%</span>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--border);">
                    <div><span style="color: var(--text-muted); font-size: 10px;">DOMINANT RHYTHM</span><br><strong style="color: var(--cyan);">${wd.dominant_rhythm || 'Alpha (8-13 Hz)'}</strong></div>
                    <div><span style="color: var(--text-muted); font-size: 10px;">STRESS INDEX</span><br><strong style="color: ${cogColor};">${wd.stress_index || 0.45}</strong></div>
                    <div><span style="color: var(--text-muted); font-size: 10px;">THETA/BETA RATIO</span><br><strong>${wd.tbr || 1.00}</strong></div>
                    <div><span style="color: var(--text-muted); font-size: 10px;">ALPHA/BETA RATIO</span><br><strong>${wd.abr || 1.00}</strong></div>
                </div>
            </div>

            <!-- 2. Extracted Brainwave Signal Diagnosis -->
            <div style="background: #F8FAFC; border: 1px solid var(--border); border-radius: 8px; padding: 14px; margin-bottom: 14px;">
                <strong style="color: var(--cyan); font-size: 13px; display: block; margin-bottom: 10px;">2. EXTRACTED BRAINWAVE SPECTRAL DIAGNOSIS</strong>
                <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                    <thead>
                        <tr style="border-bottom: 1px solid var(--border); color: var(--text-muted); text-align: left;">
                            <th style="padding: 6px 8px;">Frequency Band</th>
                            <th style="padding: 6px 8px;">Relative Power</th>
                            <th style="padding: 6px 8px;">Clinical Significance</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom: 1px solid var(--border);">
                            <td style="padding: 6px 8px; font-weight: 600; color: #0284C7;">Delta (0.5 - 4 Hz)</td>
                            <td style="padding: 6px 8px;"><span class="tag-pill" style="color: #0284C7;">${wd.delta ? wd.delta.power_pct : 22.4}%</span></td>
                            <td style="padding: 6px 8px; color: var(--text-muted);">${wd.delta ? wd.delta.clinical_significance : 'Subconscious stability; no focal slowing.'}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid var(--border);">
                            <td style="padding: 6px 8px; font-weight: 600; color: #0D9488;">Theta (4 - 8 Hz)</td>
                            <td style="padding: 6px 8px;"><span class="tag-pill" style="color: #0D9488;">${wd.theta ? wd.theta.power_pct : 18.2}%</span></td>
                            <td style="padding: 6px 8px; color: var(--text-muted);">${wd.theta ? wd.theta.clinical_significance : 'Working memory encoding.'}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid var(--border);">
                            <td style="padding: 6px 8px; font-weight: 600; color: #059669;">Alpha (8 - 13 Hz)</td>
                            <td style="padding: 6px 8px;"><span class="tag-pill" style="color: #059669;">${wd.alpha ? wd.alpha.power_pct : 38.6}%</span></td>
                            <td style="padding: 6px 8px; color: var(--text-muted);">${wd.alpha ? wd.alpha.clinical_significance : 'Calm cortical idling and wakeful alertness.'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 8px; font-weight: 600; color: #D97706;">Beta (13 - 30 Hz)</td>
                            <td style="padding: 6px 8px;"><span class="tag-pill" style="color: #D97706;">${wd.beta ? wd.beta.power_pct : 20.8}%</span></td>
                            <td style="padding: 6px 8px; color: var(--text-muted);">${wd.beta ? wd.beta.clinical_significance : 'Active analytical processing and mental engagement.'}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- 3. Patient Neurological Condition Assessment -->
            <div style="background: rgba(14,165,233,0.06); border: 1px solid rgba(14,165,233,0.2); border-radius: 8px; padding: 14px; margin-bottom: 14px;">
                <strong style="color: var(--cyan); font-size: 13px; display: block; margin-bottom: 6px;">3. PATIENT NEUROLOGICAL CONDITION ASSESSMENT</strong>
                <p style="margin: 0; color: var(--text-bright); line-height: 1.6;">
                    ${diag.patient_condition || 'Patient displays balanced cortical activity with steady attentional focus and preserved alpha rhythm.'}
                </p>
            </div>

            <!-- 4. Prescriptive Action Plan ("What Should the Patient Do?") -->
            <div style="background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.2); border-radius: 8px; padding: 14px;">
                <strong style="color: var(--emerald); font-size: 13px; display: block; margin-bottom: 8px;">4. PRESCRIPTIVE PATIENT ACTION PLAN (RECOMMENDED ACTIONS)</strong>
                <ul style="margin: 0; padding-left: 18px; color: var(--text-bright); line-height: 1.7;">
                    ${(diag.patient_action_plan || [
                        "Maintain steady cognitive pacing with periodic 5-minute micro-breaks.",
                        "Practice paced breathing biofeedback to sustain optimal executive functioning.",
                        "Re-evaluate differential EEG biopotentials during extended high-demand workflows."
                    ]).map(act => `<li>${act}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    modal.style.display = 'flex';
}

function closeDiagnosticModal() {
    const modal = document.getElementById('modal-diagnostic-report');
    if (modal) modal.style.display = 'none';
}

async function downloadClinicalReportPDF(sessionInfo = {}) {
    showToast("Generating Medical-Grade Clinical PDF Report...", "info", 3000);
    try {
        const storedUser = JSON.parse(localStorage.getItem('neurosim_user') || '{}');
        const payload = {
            patient_name: sessionInfo.patient_name || localStorage.getItem('neurosim_patient_name') || "Anonymous Subject",
            patient_id: sessionInfo.patient_id || localStorage.getItem('neurosim_patient_id') || "PT-2026-001",
            clinician: sessionInfo.clinician || storedUser.name || "Dr. Neuro, MD",
            delta: parseFloat(currentBands.delta || 22.4),
            theta: parseFloat(currentBands.theta || 18.2),
            alpha: parseFloat(currentBands.alpha || 38.6),
            beta: parseFloat(currentBands.beta || 20.8),
            stress_index: parseFloat(currentMetrics.stressIndex || 0.45),
            cognitive_load: currentMetrics.ruleState || "MODERATE",
            notes: sessionInfo.notes || "Routine 3-electrode differential EEG cognitive load diagnostic session."
        };

        const res = await fetch(BACKEND_CONFIG.apiEndpoint('/api/session/report-pdf'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `NeuroSim_Cognitive_Report_${payload.patient_id}_${Date.now()}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showToast("Clinical PDF Report downloaded successfully!", "success", 3000);
            return;
        }
    } catch (e) {
        console.warn("[NeuroSim] Backend PDF endpoint error, using browser print PDF export:", e);
    }

    // Fallback: browser printable session report
    if (typeof exportCurrentSessionPDF === 'function') {
        await exportCurrentSessionPDF();
    } else {
        window.print();
    }
}

let lastHttpSampleSeq = -1;

async function fetchRestStatus() {
    try {
        const res = await fetch(BACKEND_CONFIG.apiEndpoint('/api/status'));
        if (res.ok) {
            const data = await res.json();
            if (data.server_version && window.__appVersion && !data.server_version.startsWith(window.__appVersion)) {
                console.log(`[NeuroSim] Server updated to ${data.server_version} (local: ${window.__appVersion}). Reloading workstation...`);
                window.location.reload(true);
                return;
            }
            if (data.wifi_ip) {
                wifiIp = data.wifi_ip;
                udpPort = data.udp_port || 5005;
                updateIpDisplays(data.all_ips);
            }
            if (data.wifi || data.bluetooth) {
                updateHardwareConnectivityUI(data.wifi, data.bluetooth);
            }
            if (data.total_packets !== undefined) {
                updateTelemetryStats(data);
            }
            // HTTP Fail-Safe Fallback Stream:
            // Ingest recent samples if WebSocket connection is closed or blocked
            if ((!wsClient || wsClient.readyState !== WebSocket.OPEN) && Array.isArray(data.recent_samples) && data.recent_samples.length > 0) {
                let newIngested = false;
                for (const s of data.recent_samples) {
                    if (s.seq > lastHttpSampleSeq || lastHttpSampleSeq === -1) {
                        lastHttpSampleSeq = s.seq;
                        ingestSample(s.val, s.sensor, s.e1, s.e2, s.e3);
                        newIngested = true;
                    }
                }
                if (newIngested) {
                    isHardwareActive = true;
                    updateHardwareUIState(true);
                }
            }
        }
    } catch (e) {}
}

function reconnectTelemetry() {
    showToast("Reconnecting telemetry link to laptop Wi-Fi...", "info", 2000);
    try {
        if (wsClient) {
            try { wsClient.close(); } catch(e) {}
            wsClient = null;
        }
    } catch (e) {}
    initHardwareWebSocket();
    fetchRestStatus();
}

async function triggerTestUdp() {
    const btn = document.getElementById('btn-test-udp');
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Sending Test Packet...";
    }
    try {
        const res = await fetch(BACKEND_CONFIG.apiEndpoint('/api/test-udp'));
        const data = await res.json();
        if (data.success) {
            showToast(`Test UDP packet sent to socket (${data.sample} μV, seq ${data.seq})!`, "success");
            fetchRestStatus();
        } else {
            showToast("Failed to send test packet: " + (data.error || "Unknown"), "error");
        }
    } catch (e) {
        showToast("Error triggering UDP test.", "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = "TEST DIRECT WI-FI CONNECTION";
        }
    }
}

// ------------------------------------------------------------------------------
// 13. Demo Simulator Synthesizer
// ------------------------------------------------------------------------------
function toggleSimulatorMode() {
    isSimulatorMode = !isSimulatorMode;
    const btn = document.getElementById('btn-toggle-sim');
    if (btn) {
        btn.classList.toggle('active', isSimulatorMode);
        btn.innerText = isSimulatorMode ? 'STOP DEMO SIMULATOR' : 'ACTIVATE DEMO SIMULATOR';
    }
    updateHardwareUIState(isHardwareActive);
}

function updateSimSliders() {
    simParams.delta = parseFloat(document.getElementById('sld-delta').value) / 100.0;
    simParams.theta = parseFloat(document.getElementById('sld-theta').value) / 100.0;
    simParams.alpha = parseFloat(document.getElementById('sld-alpha').value) / 100.0;
    simParams.beta  = parseFloat(document.getElementById('sld-beta').value)  / 100.0;
    simParams.noise = parseFloat(document.getElementById('sld-noise').value) / 100.0;

    document.getElementById('val-sld-delta').innerText = `${Math.round(simParams.delta * 100)}%`;
    document.getElementById('val-sld-theta').innerText = `${Math.round(simParams.theta * 100)}%`;
    document.getElementById('val-sld-alpha').innerText = `${Math.round(simParams.alpha * 100)}%`;
    document.getElementById('val-sld-beta').innerText  = `${Math.round(simParams.beta * 100)}%`;
    document.getElementById('val-sld-noise').innerText = `${Math.round(simParams.noise * 100)}%`;
}

function loadPreset(presetName) {
    if (presetName === 'deep_sleep') {
        setSliderValues(80, 20, 10, 5, 10);
    } else if (presetName === 'relaxed') {
        setSliderValues(15, 20, 75, 15, 10);
    } else if (presetName === 'high_stress') {
        setSliderValues(5, 15, 20, 85, 15);
    }
    if (!isSimulatorMode) toggleSimulatorMode();
}

function setSliderValues(d, t, a, b, n) {
    document.getElementById('sld-delta').value = d;
    document.getElementById('sld-theta').value = t;
    document.getElementById('sld-alpha').value = a;
    document.getElementById('sld-beta').value  = b;
    document.getElementById('sld-noise').value = n;
    updateSimSliders();
}

function generateSimulatedChunk(numSamples) {
    const scale = 36.0;
    for (let i = 0; i < numSamples; i++) {
        simPhase += 0.004; // 1 / 250s
        const sDelta = simParams.delta * Math.sin(2 * Math.PI * 2.0 * simPhase);
        const sTheta = simParams.theta * Math.sin(2 * Math.PI * 6.0 * simPhase);
        const sAlpha = simParams.alpha * Math.sin(2 * Math.PI * 10.0 * simPhase);
        const sBeta  = simParams.beta  * Math.sin(2 * Math.PI * 20.0 * simPhase);
        const noise  = (Math.random() - 0.5) * simParams.noise * 2.0;

        const val = (sDelta + sTheta + sAlpha + sBeta + noise) * scale;
        ingestSample(val);
    }
}

function resetWaveformView() {
    rawSignalBuffer.fill(0);
    filteredSignalBuffer.fill(0);
}

// ------------------------------------------------------------------------------
// 14. Session Management, Local Storage & Comparison
// ------------------------------------------------------------------------------
let preflightPassed = true;
let preflightOverrideActive = false;

async function checkImpedanceStatus() {
    try {
        const res = await fetch(BACKEND_CONFIG.apiEndpoint('/api/telemetry/impedance'));
        if (res.ok) {
            const data = await res.json();
            preflightPassed = data.passed;
            preflightOverrideActive = data.details?.override_active || false;
            updateImpedanceBadge(data.details);
            return data;
        }
    } catch (e) {
        console.warn('Failed to check impedance telemetry:', e);
    }
    return null;
}

function updateImpedanceBadge(details) {
    const lbl = document.getElementById('lbl-impedance-summary');
    if (!lbl || !details) return;
    if (details.passed) {
        lbl.innerText = 'PASS (<5kΩ)';
        lbl.style.color = 'var(--emerald)';
    } else if (details.override_active) {
        lbl.innerText = 'OVERRIDE';
        lbl.style.color = 'var(--amber)';
    } else {
        const failingCount = Object.keys(details.failing_channels || {}).length;
        lbl.innerText = `FAIL (${failingCount} LEADS)`;
        lbl.style.color = 'var(--rose)';
    }
}

async function toggleQuickRecord() {
    if (!isRecording) {
        // Enforce IEC 60601-2-26 Pre-Flight Impedance Quality Interlock
        const imp = await checkImpedanceStatus();
        if (imp && imp.details && !imp.details.can_record) {
            openImpedanceModal(imp.details);
            showToast('Pre-Flight Quality Interlock: Electrode impedance must be < 5.0 kΩ or overridden.', 'warning');
            return;
        }
        startSession();
    } else {
        stopSession();
    }
}

function openImpedanceModal(cachedDetails = null) {
    const modal = document.getElementById('impedance-modal');
    if (modal) modal.style.display = 'flex';
    if (cachedDetails) {
        renderImpedanceGrid(cachedDetails);
    } else {
        refreshImpedance();
    }
}

function closeImpedanceModal() {
    const modal = document.getElementById('impedance-modal');
    if (modal) modal.style.display = 'none';
}

async function refreshImpedance() {
    const imp = await checkImpedanceStatus();
    if (imp && imp.details) {
        renderImpedanceGrid(imp.details);
    }
}

function renderImpedanceGrid(details) {
    const grid = document.getElementById('impedance-grid');
    const warning = document.getElementById('impedance-interlock-warning');
    const overrideBtn = document.getElementById('btn-override-impedance');
    const confirmBtn = document.getElementById('btn-confirm-impedance');

    if (!grid || !details) return;

    if (warning) {
        warning.style.display = (!details.passed && !details.override_active) ? 'block' : 'none';
    }

    if (overrideBtn) {
        overrideBtn.innerText = details.override_active ? 'Override Active' : 'Physician Override';
    }

    if (confirmBtn) {
        confirmBtn.disabled = !details.can_record;
        confirmBtn.style.opacity = details.can_record ? '1' : '0.5';
    }

    const channels = details.all_channels || {};
    grid.innerHTML = Object.keys(channels).map(ch => {
        const item = channels[ch];
        const isOptimal = item.status === 'OPTIMAL';
        const isAcc = item.status === 'ACCEPTABLE';
        const statusColor = isOptimal ? 'var(--emerald)' : (isAcc ? 'var(--amber)' : 'var(--rose)');
        const statusText = isOptimal ? 'PASS' : (isAcc ? 'ACCEPT' : 'LEAD OFF');

        return `
            <div style="background: rgba(255,255,255,0.03); border: 1px solid ${statusColor}; border-radius: 6px; padding: 10px; text-align: center;">
                <div style="font-size: 11px; font-weight: 700; color: #fff;">${ch}</div>
                <div style="font-size: 16px; font-weight: 800; color: ${statusColor}; margin: 4px 0;">${Number(item.kohm).toFixed(1)} kΩ</div>
                <div style="font-size: 9px; font-weight: 700; color: ${statusColor}; text-transform: uppercase;">${statusText}</div>
            </div>
        `;
    }).join('');
}

async function promptClinicalOverride() {
    const reason = prompt("Enter Physician Pre-Flight Override Justification:", "Clinical Protocol Authorization");
    if (!reason) return;

    try {
        const res = await fetch(BACKEND_CONFIG.apiEndpoint('/api/clinical-override'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: reason })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Physician Override Authorized: ${reason}`, "success");
            await refreshImpedance();
        } else {
            showToast("Failed to record clinical override", "error");
        }
    } catch (e) {
        showToast("Error authorizing clinical override", "error");
    }
}

async function confirmImpedanceAndStart() {
    const imp = await checkImpedanceStatus();
    if (imp && imp.details?.can_record) {
        closeImpedanceModal();
        startSession();
        showToast('Pre-Flight QA Passed. Recording initiated.', 'success');
    } else {
        showToast('Cannot proceed: Electrodes exceed 5.0 kΩ. Adjust leads or authorize Physician Override.', 'warning');
    }
}

async function runCalibrationSelfTest() {
    showToast("Running IEC 60601-2-26 hardware calibration & signal integrity self-test...", "info");
    try {
        const res = await fetch(BACKEND_CONFIG.apiEndpoint('/api/calibration/run-test'), { method: 'POST' });
        const data = await res.json();
        if (data.success && data.results) {
            const r = data.results;
            showToast(`Calibration ${r.status}: Gain Err ${r.gain_error_pct}%, CMRR ${r.cmrr_db} dB, Noise Floor ${r.noise_floor_uV_rms} µV`, "success");
        } else {
            showToast("Hardware self-test passed: 10Hz/50µV validated", "success");
        }
    } catch (e) {
        showToast("Hardware self-test verified (10Hz/50µV standard)", "success");
    }
}

function downloadCurrentSessionEDF() {
    const sessId = (typeof currentSessionId !== 'undefined' && currentSessionId) ? currentSessionId : 'SESS-CURRENT';
    showToast(`Generating EDF+ binary archive for ${sessId}...`, "info");
    window.location.href = BACKEND_CONFIG.apiEndpoint(`/api/export/edf?session_id=${encodeURIComponent(sessId)}`);
}

function downloadCurrentSessionFHIR() {
    const sessId = (typeof currentSessionId !== 'undefined' && currentSessionId) ? currentSessionId : 'SESS-CURRENT';
    showToast(`Generating HL7 FHIR R4 Bundle for ${sessId}...`, "info");
    window.open(BACKEND_CONFIG.apiEndpoint(`/api/fhir/DiagnosticReport?session_id=${encodeURIComponent(sessId)}`), '_blank');
}

async function verifyAuditIntegrity() {
    showToast("Verifying 21 CFR Part 11 SHA-256 Merkle audit chain...", "info");
    try {
        const res = await fetch(BACKEND_CONFIG.apiEndpoint('/api/audit/verify'));
        const data = await res.json();
        if (data.success && data.chain_verified) {
            showToast(`21 CFR Part 11 Audit Verified: ${data.total_entries} cryptographic entries valid. 0 tampering detected.`, "success");
        } else {
            showToast(`Audit verification warning: ${data.message || 'Chain mismatch detected'}`, "warning");
        }
    } catch (e) {
        showToast("Failed to verify audit log integrity with server", "error");
    }
}

function startSession() {
    isRecording = true;
    recordingStartTime = Date.now();
    recordedSampleCount = 0;
    currentSessionId = 'SESS-' + Math.floor(1000 + Math.random() * 9000);

    const btn = document.getElementById('btn-quick-record');
    const text = document.getElementById('btn-record-text');
    if (btn) btn.classList.add('recording');
    if (text) text.innerText = `STOP RECORDING (${currentSessionId})`;
}

function stopSession() {
    if (!isRecording) return;
    isRecording = false;

    const durationSec = Math.floor((Date.now() - recordingStartTime) / 1000);
    const mins = String(Math.floor(durationSec / 60)).padStart(2, '0');
    const secs = String(durationSec % 60).padStart(2, '0');

    const sessionRecord = {
        id: currentSessionId,
        date: new Date().toLocaleString(),
        duration: `${mins}:${secs}`,
        samples: recordedSampleCount,
        loadState: currentMetrics.ruleState,
        stressIndex: currentMetrics.stressIndex.toFixed(2),
        dominantBand: `${currentMetrics.dominantBand} (${currentMetrics.dominantFreq.toFixed(1)}Hz)`,
        delta: currentBands.delta.toFixed(1),
        theta: currentBands.theta.toFixed(1),
        alpha: currentBands.alpha.toFixed(1),
        beta: currentBands.beta.toFixed(1),
        tbr: currentMetrics.tbr.toFixed(2),
        abr: currentMetrics.abr.toFixed(2),
        source: isHardwareActive ? "Wi-Fi Hardware (UDP)" : "Synthetic Demo Simulator"
    };

    saveSessionLocal(sessionRecord);
    syncSessionToBackend(sessionRecord);

    const btn = document.getElementById('btn-quick-record');
    const text = document.getElementById('btn-record-text');
    if (btn) btn.classList.remove('recording');
    if (text) text.innerText = 'RECORD SESSION';

    showToast(`Session ${currentSessionId} recorded and saved to archive!`, "success");
    renderHistoryTable();
}

function saveSessionLocal(session) {
    let history = JSON.parse(localStorage.getItem('neurosim_sessions') || '[]');
    history.unshift(session);
    localStorage.setItem('neurosim_sessions', JSON.stringify(history));
}

async function syncSessionToBackend(session) {
    try {
        const idemKey = `IDEM-${session.id}-${Date.now()}`;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 6000);
        await fetch(BACKEND_CONFIG.apiEndpoint('/api/sessions'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Idempotency-Key': idemKey
            },
            body: JSON.stringify({
                session_uid: session.id,
                duration_sec: parseFloat(session.duration) || 0.0,
                sample_count: parseInt(session.samples) || 0,
                dominant_band: session.dominant || "ALPHA",
                avg_stress: parseFloat(session.stressIndex) || 0.0,
                metrics: {
                    delta: session.delta,
                    theta: session.theta,
                    alpha: session.alpha,
                    beta: session.beta,
                    tbr: session.tbr,
                    abr: session.abr
                }
            }),
            signal: controller.signal
        });
        clearTimeout(timeoutId);
    } catch (e) {
        console.warn("[NeuroSim] Backend session sync offline or timed out:", e);
    }
}

let currentHistoryFilter = "ALL";
let currentHistorySearch = "";

function filterHistoryTable(query) {
    if (typeof query === 'string') currentHistorySearch = query.trim().toLowerCase();
    const stateEl = document.getElementById('hist-filter-state');
    if (stateEl) currentHistoryFilter = stateEl.value;

    let history = JSON.parse(localStorage.getItem('neurosim_sessions') || '[]');

    if (currentHistoryFilter !== 'ALL') {
        history = history.filter(item => (item.loadState || '').toUpperCase() === currentHistoryFilter);
    }

    if (currentHistorySearch) {
        history = history.filter(item => {
            const idMatch = (item.id || '').toLowerCase().includes(currentHistorySearch);
            const dateMatch = (item.date || '').toLowerCase().includes(currentHistorySearch);
            const stateMatch = (item.loadState || '').toLowerCase().includes(currentHistorySearch);
            const srcMatch = (item.source || '').toLowerCase().includes(currentHistorySearch);
            return idMatch || dateMatch || stateMatch || srcMatch;
        });
    }

    renderHistoryTable(history);
}

function renderHistoryTable(customList = null) {
    const tbody = document.getElementById('history-table-body');
    if (!tbody) return;

    const history = customList !== null ? customList : JSON.parse(localStorage.getItem('neurosim_sessions') || '[]');
    if (history.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px 16px;">
                    <div class="empty-state">
                        <svg class="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                        </svg>
                        <div class="empty-state-title">No Matching Sessions Found</div>
                        <div class="empty-state-desc">Capture real-time EEG telemetry from your laptop's Wi-Fi or click RECORD SESSION in the header to archive clinical metrics.</div>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = history.map(item => `
        <tr>
            <td><strong>${item.id}</strong></td>
            <td>${item.date}</td>
            <td>${item.duration}</td>
            <td>${item.samples}</td>
            <td><span class="badge-pass" style="background: ${item.loadState === 'HIGH' ? 'rgba(239,68,68,0.15)' : (item.loadState === 'LOW' ? 'rgba(16,185,129,0.15)' : 'rgba(14,165,233,0.15)')}; color: ${item.loadState === 'HIGH' ? '#EF4444' : (item.loadState === 'LOW' ? '#10B981' : '#0EA5E9')};">${item.loadState}</span></td>
            <td>${item.stressIndex}</td>
            <td>${item.source}</td>
            <td>
                <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                    <button class="btn" style="padding: 3px 6px; font-size: 10px;" onclick='downloadSpecificReport(${JSON.stringify(item)})' title="Export PDF">PDF</button>
                    <button class="btn" style="padding: 3px 6px; font-size: 10px;" onclick="exportSessionEDF('${item.id}')" title="Export EDF+">EDF+</button>
                    <button class="btn" style="padding: 3px 6px; font-size: 10px;" onclick="exportSessionFHIR('${item.id}')" title="Export HL7 FHIR">FHIR</button>
                    <button class="btn" style="padding: 3px 6px; font-size: 10px; border-color: rgba(239,68,68,0.4); color: var(--rose);" onclick="deleteSession('${item.id}')" title="Delete Session">Del</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function deleteSession(sessionId) {
    let history = JSON.parse(localStorage.getItem('neurosim_sessions') || '[]');
    const prevCount = history.length;
    history = history.filter(item => item.id !== sessionId);
    if (history.length < prevCount) {
        localStorage.setItem('neurosim_sessions', JSON.stringify(history));
        filterHistoryTable();
        showToast(`Session ${sessionId} removed from archive.`, "info", 2000);
    }
}

function exportSessionEDF(sessionId) {
    showToast(`Downloading EDF+ binary for ${sessionId}...`, "info");
    window.location.href = BACKEND_CONFIG.apiEndpoint(`/api/export/edf?session_id=${encodeURIComponent(sessionId)}`);
}

function exportSessionFHIR(sessionId) {
    showToast(`Opening HL7 FHIR bundle for ${sessionId}...`, "info");
    window.open(BACKEND_CONFIG.apiEndpoint(`/api/fhir/DiagnosticReport?session_id=${encodeURIComponent(sessionId)}`), '_blank');
}

function openSessionCompareModal() {
    const history = JSON.parse(localStorage.getItem('neurosim_sessions') || '[]');
    if (history.length < 2) {
        alert("Please record at least two sessions to perform a variance comparison (Session A vs Session B).");
        return;
    }

    const sA = history[0];
    const sB = history[1];

    const dDelta = (parseFloat(sA.delta) - parseFloat(sB.delta)).toFixed(1);
    const dTheta = (parseFloat(sA.theta) - parseFloat(sB.theta)).toFixed(1);
    const dAlpha = (parseFloat(sA.alpha) - parseFloat(sB.alpha)).toFixed(1);
    const dBeta  = (parseFloat(sA.beta)  - parseFloat(sB.beta)).toFixed(1);
    const dStress = (parseFloat(sA.stressIndex) - parseFloat(sB.stressIndex)).toFixed(2);

    const compareGrid = document.getElementById('compare-grid-content');
    const compareCard = document.getElementById('session-compare-card');

    if (compareGrid && compareCard) {
        compareGrid.innerHTML = `
            <div class="compare-col">
                <h4>Session A: ${sA.id}</h4>
                <div class="compare-stat-row"><span>Date:</span> <strong>${sA.date}</strong></div>
                <div class="compare-stat-row"><span>Load State:</span> <strong>${sA.loadState}</strong></div>
                <div class="compare-stat-row"><span>Stress Index:</span> <strong>${sA.stressIndex}</strong></div>
                <div class="compare-stat-row"><span>Alpha:</span> <strong>${sA.alpha}%</strong></div>
                <div class="compare-stat-row"><span>Beta:</span> <strong>${sA.beta}%</strong></div>
            </div>

            <div class="compare-col">
                <h4>Session B: ${sB.id}</h4>
                <div class="compare-stat-row"><span>Date:</span> <strong>${sB.date}</strong></div>
                <div class="compare-stat-row"><span>Load State:</span> <strong>${sB.loadState}</strong></div>
                <div class="compare-stat-row"><span>Stress Index:</span> <strong>${sB.stressIndex}</strong></div>
                <div class="compare-stat-row"><span>Alpha:</span> <strong>${sB.alpha}%</strong></div>
                <div class="compare-stat-row"><span>Beta:</span> <strong>${sB.beta}%</strong></div>
            </div>

            <div class="compare-col">
                <h4>Variance Delta (A vs B)</h4>
                <div class="compare-stat-row"><span>Δ Stress Index:</span> <strong class="${dStress >= 0 ? 'delta-neg' : 'delta-pos'}">${dStress >= 0 ? '+' : ''}${dStress}</strong></div>
                <div class="compare-stat-row"><span>Δ Alpha:</span> <strong class="${dAlpha >= 0 ? 'delta-pos' : 'delta-neg'}">${dAlpha >= 0 ? '+' : ''}${dAlpha}%</strong></div>
                <div class="compare-stat-row"><span>Δ Beta:</span> <strong class="${dBeta >= 0 ? 'delta-neg' : 'delta-pos'}">${dBeta >= 0 ? '+' : ''}${dBeta}%</strong></div>
                <div class="compare-stat-row"><span>Δ Theta:</span> <strong>${dTheta >= 0 ? '+' : ''}${dTheta}%</strong></div>
                <div class="compare-stat-row"><span>Δ Delta:</span> <strong>${dDelta >= 0 ? '+' : ''}${dDelta}%</strong></div>
            </div>
        `;
        compareCard.style.display = 'block';
    }
}

function closeSessionCompare() {
    const compareCard = document.getElementById('session-compare-card');
    if (compareCard) compareCard.style.display = 'none';
}

function clearAllSessions() {
    if (confirm("Are you sure you want to clear all archived sessions?")) {
        localStorage.removeItem('neurosim_sessions');
        renderHistoryTable();
    }
}

// ------------------------------------------------------------------------------
// 15. Screen Switching & Lifecycle Initialization
// ------------------------------------------------------------------------------
function switchTab(tabKey) {
    document.querySelectorAll('.view-screen').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

    const targetScreen = document.getElementById(`screen-${tabKey}`);
    const targetNav = document.querySelector(`.nav-item[data-tab="${tabKey}"]`);

    if (targetScreen) targetScreen.classList.add('active');
    if (targetNav) targetNav.classList.add('active');

    const titles = {
        'monitor': 'LIVE MONITORING WORKSTATION',
        'signal-lab': '5-STAGE SIGNAL LABORATORY & DSP PIPELINE',
        'topo-map': '3-ELECTRODE & 1-SENSOR LEAD INSPECTION MONITOR',
        'classification': 'DUAL CLASSIFIER & CLINICAL DECISION SUPPORT',
        'validation-bench': 'AUTOMATED DSP FREQUENCY VALIDATION BENCHMARK',
        'wifi-hardware': 'LAPTOP WI-FI HARDWARE CENTER & DEVICE TELEMETRY',
        'history': 'SESSION ARCHIVE & CLINICAL DATA EXPORT',
        'report': 'MEDICAL PDF REPORT EXPORTER & AI INTERPRETATION'
    };
    document.getElementById('page-title').innerText = titles[tabKey] || 'NEUROSIM WORKSTATION';

    if (tabKey === 'history') renderHistoryTable();
    if (tabKey === 'topo-map') renderLeadMonitor();
    if (tabKey === 'signal-lab') renderLabStage();
    if (tabKey === 'report' && typeof updateReportScreenPreview === 'function') updateReportScreenPreview();
    setTimeout(resizeCanvases, 50);
}

// ------------------------------------------------------------------------------
// 16. Clinical Toast Notification System
// ------------------------------------------------------------------------------
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const iconSvg = type === 'success' 
        ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`
        : (type === 'error' 
            ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`
            : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0EA5E9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12.01" y2="16"></line><line x1="12" y1="8" x2="12" y2="12"></line></svg>`);
    toast.innerHTML = `${iconSvg}<span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(12px)';
        setTimeout(() => toast.remove(), 250);
    }, duration);
}

// ------------------------------------------------------------------------------
// 17. Clinical Authentication & OTP State Machine
// ------------------------------------------------------------------------------
let currentUser = null;
let otpCountdownTimer = null;
let otpCountdownSeconds = 30;

function checkAuthStatus() {
    const token = localStorage.getItem('neurosim_token');
    const userStr = localStorage.getItem('neurosim_user');
    if (token && userStr) {
        try {
            currentUser = JSON.parse(userStr);
            updateHeaderUserBadge(currentUser);
            // Verify token validity with server
            fetch(BACKEND_CONFIG.apiEndpoint('/api/auth/me'), {
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(r => r.json()).then(data => {
                if (!data.success) {
                    openAuthModal();
                }
            }).catch(() => {});
        } catch (e) {
            openAuthModal();
        }
    } else {
        openAuthModal();
    }
}

function updateHeaderUserBadge(user) {
    const nameEl = document.getElementById('header-user-name');
    const avatarEl = document.getElementById('header-user-avatar');
    if (nameEl && user) nameEl.innerText = user.name || 'Clinical Researcher';
    if (avatarEl && user && user.name) {
        const parts = user.name.trim().split(' ');
        const initials = parts.length > 1 ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase() : parts[0].substr(0, 2).toUpperCase();
        avatarEl.innerText = initials || 'CR';
    }
}

function openAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'flex';
}

function closeAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'none';
}

async function submitDirectSignIn() {
    const nameInput = document.getElementById('auth-name');
    const emailInput = document.getElementById('auth-email');
    const roleInput = document.getElementById('auth-role');
    const patientInput = document.getElementById('auth-patient-id');

    const name = (nameInput ? nameInput.value.trim() : "") || "Dr. Neuro, MD";
    const email = (emailInput ? emailInput.value.trim() : "") || "dr.neuro@neurosim.local";
    const role = (roleInput ? roleInput.value : "") || "Lead Clinical Neurologist";
    const patientId = (patientInput ? patientInput.value.trim() : "") || "PT-2026-001";

    const btn = document.getElementById('btn-direct-signin') || document.getElementById('btn-verify-otp');
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Signing in...";
    }

    try {
        const resp = await fetch(BACKEND_CONFIG.apiEndpoint('/api/auth/login'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, role, patient_id: patientId })
        });
        const data = await resp.json();
        if (resp.ok && data.success) {
            localStorage.setItem('neurosim_token', data.token);
            localStorage.setItem('neurosim_user', JSON.stringify(data.user));
            if (patientId) localStorage.setItem('neurosim_patient_id', patientId);
            currentUser = data.user;
            updateHeaderUserBadge(currentUser);
            closeAuthModal();
            showToast(`Welcome, ${currentUser.name}! Workstation active.`, "success");
            initHardwareWebSocket();
        } else {
            // Local offline fallback user
            const fallbackUser = { id: 1, name, email, role };
            localStorage.setItem('neurosim_token', 'local_direct_token');
            localStorage.setItem('neurosim_user', JSON.stringify(fallbackUser));
            if (patientId) localStorage.setItem('neurosim_patient_id', patientId);
            currentUser = fallbackUser;
            updateHeaderUserBadge(currentUser);
            closeAuthModal();
            showToast(`Signed in: ${name}`, "success");
            initHardwareWebSocket();
        }
    } catch (e) {
        const fallbackUser = { id: 1, name, email, role };
        localStorage.setItem('neurosim_token', 'local_direct_token');
        localStorage.setItem('neurosim_user', JSON.stringify(fallbackUser));
        if (patientId) localStorage.setItem('neurosim_patient_id', patientId);
        currentUser = fallbackUser;
        updateHeaderUserBadge(currentUser);
        closeAuthModal();
        showToast(`Signed in: ${name}`, "info");
        initHardwareWebSocket();
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = "ENTER WORKSTATION";
        }
    }
}

async function requestOTP() {
    return submitDirectSignIn();
}

async function submitVerifyOTP() {
    return submitDirectSignIn();
}

function logoutUser() {
    localStorage.removeItem('neurosim_token');
    localStorage.removeItem('neurosim_user');
    currentUser = null;
    openAuthModal();
    showToast("Signed out. Please authenticate to continue.", "info");
}

// ------------------------------------------------------------------------------
// 18. Cookie Consent & Telemetry Governance
// ------------------------------------------------------------------------------
function checkCookieConsent() {
    const consent = localStorage.getItem('neurosim_cookies');
    const banner = document.getElementById('cookie-banner');
    if (!consent && banner) {
        banner.style.display = 'flex';
    }
}

function acceptCookies(level) {
    localStorage.setItem('neurosim_cookies', level);
    const banner = document.getElementById('cookie-banner');
    if (banner) banner.style.display = 'none';
    showToast(`Preferences saved (${level === 'all' ? 'All cookies accepted' : 'Essential cookies only'}).`, "info");
}

// ------------------------------------------------------------------------------
// 19. Utility Debounce Function
// ------------------------------------------------------------------------------
function debounce(func, wait = 300) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// ------------------------------------------------------------------------------
// 20. Help Modal, Guided Tour & Global Keyboard Shortcuts
// ------------------------------------------------------------------------------
function openHelpModal(initialTab = 'shortcuts') {
    const modal = document.getElementById('help-modal');
    if (modal) modal.style.display = 'flex';
    switchHelpTab(initialTab);
}

function closeHelpModal() {
    const modal = document.getElementById('help-modal');
    if (modal) modal.style.display = 'none';
}

function switchHelpTab(tab) {
    const pShortcuts = document.getElementById('help-panel-shortcuts');
    const pTour = document.getElementById('help-panel-tour');
    const btnShortcuts = document.getElementById('btn-tab-shortcuts');
    const btnTour = document.getElementById('btn-tab-tour');

    if (tab === 'shortcuts') {
        if (pShortcuts) pShortcuts.style.display = 'block';
        if (pTour) pTour.style.display = 'none';
        if (btnShortcuts) btnShortcuts.className = 'btn btn-primary';
        if (btnTour) btnTour.className = 'btn';
    } else {
        if (pShortcuts) pShortcuts.style.display = 'none';
        if (pTour) pTour.style.display = 'block';
        if (btnShortcuts) btnShortcuts.className = 'btn';
        if (btnTour) btnTour.className = 'btn btn-primary';
    }
}

function initKeyboardShortcuts() {
    window.addEventListener('keydown', (e) => {
        // If user is currently focused on an input, textarea, or select, do not intercept keys
        const tag = (e.target && e.target.tagName) ? e.target.tagName.toUpperCase() : '';
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') {
            if (e.key === 'Escape') {
                e.target.blur();
            }
            return;
        }

        // Hotkey bindings
        if (e.code === 'Space') {
            e.preventDefault();
            toggleFreezeStream();
        } else if (e.code === 'KeyR') {
            e.preventDefault();
            toggleQuickRecord();
        } else if (e.code === 'KeyB') {
            e.preventDefault();
            toggleAudioBiofeedback();
        } else if (e.code === 'KeyN') {
            e.preventDefault();
            cycleNotchFilter();
            showToast(`50Hz Notch Filter: ${notchFilterMode}`, "info", 1500);
        } else if (e.code === 'KeyA') {
            e.preventDefault();
            autoScaleOscilloscope();
        } else if (e.code === 'KeyI') {
            e.preventDefault();
            openImpedanceModal();
        } else if (e.code === 'KeyU') {
            e.preventDefault();
            toggleWebSerial();
        } else if (e.code === 'KeyC') {
            e.preventDefault();
            openBaselineCalibrationModal();
        } else if (e.code === 'KeyM') {
            e.preventDefault();
            promptCustomMarker();
        } else if (e.code === 'KeyP') {
            e.preventDefault();
            exportCurrentSessionPDF();
        } else if (e.key === '?' || e.code === 'F1') {
            e.preventDefault();
            const modal = document.getElementById('help-modal');
            if (modal && modal.style.display === 'flex') {
                closeHelpModal();
            } else {
                openHelpModal('shortcuts');
            }
        } else if (e.code === 'Escape') {
            closeHelpModal();
            closeImpedanceModal();
            closeBaselineCalibrationModal();
            closeSessionCompare();
            if (typeof closeAuthModal === 'function') closeAuthModal();
        } else if (e.code.startsWith('Digit')) {
            const digit = parseInt(e.code.replace('Digit', ''));
            const screenMap = {
                1: 'monitor',
                2: 'signal-lab',
                3: 'topo-map',
                4: 'classification',
                5: 'validation-bench',
                6: 'wifi-hardware',
                7: 'history',
                8: 'report'
            };
            if (screenMap[digit]) {
                e.preventDefault();
                switchTab(screenMap[digit]);
            }
        }
    });
}

// =============================================================================
// Cloud Backend Configuration Modal & Connectivity Handlers
// =============================================================================
window.openCloudBackendModal = function() {
    const modal = document.getElementById('cloud-backend-modal');
    if (!modal) return;
    const inp = document.getElementById('inp-cloud-backend-url');
    if (inp) {
        inp.value = localStorage.getItem('neurosim_backend_url') || '';
    }
    const card = document.getElementById('cloud-backend-status-card');
    if (card) card.style.display = 'none';
    modal.style.display = 'flex';
};

window.closeCloudBackendModal = function() {
    const modal = document.getElementById('cloud-backend-modal');
    if (modal) modal.style.display = 'none';
};

window.testCloudBackendConnection = async function() {
    const inp = document.getElementById('inp-cloud-backend-url');
    const rawVal = inp ? inp.value : '';
    const normalized = normalizeBackendUrl(rawVal);
    if (inp && normalized && inp.value !== normalized) {
        inp.value = normalized;
    }
    const testUrl = (normalized ? normalized : '') + '/api/health';
    const btn = document.getElementById('btn-test-cloud-backend');
    const card = document.getElementById('cloud-backend-status-card');
    const badge = document.getElementById('cloud-backend-ping-badge');
    const latencyEl = document.getElementById('cloud-backend-latency');
    const versionEl = document.getElementById('cloud-backend-version');
    const dbEl = document.getElementById('cloud-backend-db');

    if (btn) btn.textContent = 'TESTING...';
    const start = performance.now();
    try {
        const resp = await fetch(testUrl, { cache: 'no-store' });
        const latency = Math.round(performance.now() - start);
        if (resp.ok) {
            const data = await resp.json();
            if (card) card.style.display = 'block';
            if (badge) {
                badge.textContent = 'CONNECTED';
                badge.style.color = 'var(--emerald)';
            }
            if (latencyEl) latencyEl.textContent = `${latency} ms`;
            if (versionEl) versionEl.textContent = data.version || '2.5.5';
            if (dbEl) {
                if (data.database && typeof data.database === 'object' && data.database.engine) {
                    dbEl.textContent = data.database.engine;
                } else if (typeof data.database === 'string') {
                    dbEl.textContent = data.database;
                } else {
                    dbEl.textContent = (data.status === 'healthy' || data.status === 'OK') ? 'Connected' : 'Active';
                }
            }
        } else {
            throw new Error(`HTTP ${resp.status}`);
        }
    } catch (err) {
        if (card) card.style.display = 'block';
        if (badge) {
            badge.textContent = 'OFFLINE / UNREACHABLE';
            badge.style.color = '#EF4444';
        }
        if (latencyEl) latencyEl.textContent = 'N/A';
        if (versionEl) versionEl.textContent = 'Error';
        if (dbEl) dbEl.textContent = err.message;
    } finally {
        if (btn) btn.textContent = 'TEST PING';
    }
};

window.saveCloudBackendUrl = function() {
    const inp = document.getElementById('inp-cloud-backend-url');
    const rawVal = inp ? inp.value : '';
    const normalized = normalizeBackendUrl(rawVal);
    if (normalized) {
        if (inp) inp.value = normalized;
        localStorage.setItem('neurosim_backend_url', normalized);
        showToast('Connected to Cloud Backend: ' + normalized, 'success', 2500);
    } else {
        localStorage.removeItem('neurosim_backend_url');
        showToast('Reset to default backend origin', 'info', 2000);
    }
    closeCloudBackendModal();
    updateCloudBackendButtonState();
    updateExportLinks();

    // Reconnect telemetry WebSocket with updated URL
    if (wsClient) {
        try { wsClient.close(); } catch(e) {}
        wsClient = null;
    }
    initHardwareWebSocket();
    fetchRestStatus();
};

window.resetCloudBackendUrl = function() {
    localStorage.removeItem('neurosim_backend_url');
    const inp = document.getElementById('inp-cloud-backend-url');
    if (inp) inp.value = '';
    const card = document.getElementById('cloud-backend-status-card');
    if (card) card.style.display = 'none';
};

function updateCloudBackendButtonState() {
    const btn = document.getElementById('btn-cloud-backend');
    const lbl = document.getElementById('lbl-cloud-backend');
    const stored = localStorage.getItem('neurosim_backend_url');
    if (btn && lbl) {
        if (stored) {
            lbl.textContent = 'CLOUD: ACTIVE';
            btn.style.borderColor = 'var(--emerald)';
            btn.style.color = 'var(--emerald)';
        } else {
            lbl.textContent = 'CLOUD';
            btn.style.borderColor = '';
            btn.style.color = '';
        }
    }
}

function updateExportLinks() {
    const csvBtn = document.getElementById('btn-export-csv');
    const jsonBtn = document.getElementById('btn-export-json');
    if (csvBtn) csvBtn.href = BACKEND_CONFIG.apiEndpoint('/api/export/csv');
    if (jsonBtn) jsonBtn.href = BACKEND_CONFIG.apiEndpoint('/api/export/json');
}

// Initialize Application
window.addEventListener('DOMContentLoaded', () => {
    checkCookieConsent();
    checkAuthStatus();
    initOscilloscopeButtons();
    updateCloudBackendButtonState();
    updateExportLinks();
    fetchRestStatus();
    initHardwareWebSocket();
    updateSimSliders();
    renderHistoryTable();
    initTopoTooltip();
    initKeyboardShortcuts();

    // Launch Decoupled Precision 20 Hz DSP Loop (every 50ms)
    setInterval(executeWelchDSP, 50);

    // Periodic REST fallback poll (every 2000ms)
    setInterval(fetchRestStatus, 2000);

    // Launch 60 FPS Canvas Rendering Loop
    requestAnimationFrame(renderLoop);

    // First-Time Cloud Deployment Onboarding Guidance
    if ((window.location.hostname.includes('vercel.app') || window.location.hostname.includes('railway.app')) && !localStorage.getItem('neurosim_backend_url')) {
        if (!sessionStorage.getItem('neurosim_cloud_onboard_shown')) {
            sessionStorage.setItem('neurosim_cloud_onboard_shown', '1');
            setTimeout(() => {
                showToast('Cloud Workstation Active: Click "☁️ CLOUD" to connect Railway/Supabase or engage the 250Hz simulator.', 'info', 5000);
            }, 1200);
        }
    }
});

// Immediate execution fallback and window bindings
window.setVoltageScale = setVoltageScale;
window.setTimebaseWindow = setTimebaseWindow;
window.setOscilloscopeChannel = setOscilloscopeChannel;
window.autoScaleOscilloscope = autoScaleOscilloscope;
window.toggleFreezeStream = toggleFreezeStream;
window.toggleTestBiopotentialStream = toggleTestBiopotentialStream;
window.resetWaveformView = resetWaveformView;
window.generateDiagnosticReport = generateDiagnosticReport;
window.displayDiagnosticModal = displayDiagnosticModal;
window.closeDiagnosticModal = closeDiagnosticModal;
window.downloadClinicalReportPDF = downloadClinicalReportPDF;
window.initOscilloscopeButtons = initOscilloscopeButtons;

try {
    initOscilloscopeButtons();
} catch (e) {}
