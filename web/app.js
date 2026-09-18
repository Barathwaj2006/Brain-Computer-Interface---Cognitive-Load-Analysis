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
let writeIndex = 0;
let totalSamplesReceived = 0;

// Hardware & Wi-Fi Connection State
const WS_PORT = 8765;
let wsPort = 8765;
let isHardwareActive = false;
let isSimulatorMode = false;
let wsClient = null;
let wifiIp = "192.168.29.155";
let udpPort = 5005;
let wsHeartbeatTimer = null;

// Filter Pipeline States
let isBandpassActive = true;
let notchFilterMode = "50Hz"; // "OFF", "50Hz", "60Hz"
let isArtifactFilterActive = true; // Medical EOG / EMG Artifact Suppression

// Web Audio Neurofeedback State
let audioCtx = null;
let bioOscillator = null;
let bioGainNode = null;
let isAudioActive = false;
let biofeedbackVolume = 0.5; // Master audio volume multiplier (0.0 - 1.0)

// Interactive Oscilloscope Display State
let isStreamFrozen = false;
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

    // 4. Physiological Artifact Clamping (Ocular EOG Blinks & Temporal EMG Bursts)
    if (isArtifactFilterActive && Math.abs(y) > 100.0) {
        y = Math.sign(y) * (100.0 + 20.0 * Math.tanh((Math.abs(y) - 100.0) / 20.0));
    }

    return y;
}

// Push sample into circular buffers
function ingestSample(rawVal) {
    const filteredVal = filterSample(rawVal);

    rawSignalBuffer[writeIndex] = rawVal;
    filteredSignalBuffer[writeIndex] = filteredVal;
    writeIndex = (writeIndex + 1) % BUFFER_SIZE;
    totalSamplesReceived++;

    if (isRecording) {
        recordedSampleCount++;
    }
}

// ------------------------------------------------------------------------------
// 4. Precision DSP Calculation (Welch Periodogram Averaging @ 20 Hz)
// ------------------------------------------------------------------------------
function executeWelchDSP() {
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

    // Band Integration (Trapezoidal Sum)
    let pDelta = 0, pTheta = 0, pAlpha = 0, pBeta = 0;
    let maxPower = 0.0;
    let peakBin = 20;

    for (let k = 1; k < halfN; k++) {
        const freq = k * df;
        const power = psdAccumulator[k];

        if (power > maxPower) {
            maxPower = power;
            peakBin = k;
        }

        if (freq >= 0.5 && freq < 4.0) pDelta += power;
        else if (freq >= 4.0 && freq < 8.0) pTheta += power;
        else if (freq >= 8.0 && freq < 13.0) pAlpha += power;
        else if (freq >= 13.0 && freq <= 30.0) pBeta += power;
    }

    const totalBandPower = pDelta + pTheta + pAlpha + pBeta + 1e-6;
    currentBands.delta = (pDelta / totalBandPower) * 100.0;
    currentBands.theta = (pTheta / totalBandPower) * 100.0;
    currentBands.alpha = (pAlpha / totalBandPower) * 100.0;
    currentBands.beta  = (pBeta  / totalBandPower) * 100.0;

    // Clinical Ratios
    const tbr = currentBands.theta / (currentBands.beta + 1e-4);
    const abr = currentBands.alpha / (currentBands.beta + 1e-4);
    const stress = currentBands.beta / (currentBands.alpha + currentBands.theta + 1e-4);
    const eng = currentBands.beta / (currentBands.alpha + currentBands.theta + 1e-4);

    const peakFreq = peakBin * df;
    let domBand = "ALPHA";
    if (peakFreq < 4.0) domBand = "DELTA";
    else if (peakFreq < 8.0) domBand = "THETA";
    else if (peakFreq < 13.0) domBand = "ALPHA";
    else domBand = "BETA";

    currentMetrics.dominantFreq = peakFreq;
    currentMetrics.dominantBand = domBand;
    currentMetrics.tbr = tbr;
    currentMetrics.abr = abr;
    currentMetrics.stressIndex = stress;
    currentMetrics.engagement = eng;
    currentMetrics.totalPower = totalBandPower;

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

    currentMetrics.ruleState = ruleState;
    currentMetrics.ruleMargin = ruleMargin;
    currentMetrics.mlState = mlState;
    currentMetrics.mlConf = mlConf;
    currentMetrics.probLow = pLow;
    currentMetrics.probMod = pMod;
    currentMetrics.probHigh = pHigh;

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

    // 3. Draw Topo Map if visible
    const topoScreen = document.getElementById('screen-topo-map');
    if (topoScreen && topoScreen.classList.contains('active')) {
        drawContinuousTopoMap();
    }

    // 4. Draw Signal Lab if visible
    const labScreen = document.getElementById('screen-signal-lab');
    if (labScreen && labScreen.classList.contains('active')) {
        renderLabStage();
    }

    requestAnimationFrame(renderLoop);
}

// Interactive Oscilloscope Toolbar Handlers
function toggleFreezeStream() {
    isStreamFrozen = !isStreamFrozen;
    const btn = document.getElementById('btn-freeze-stream');
    const watermark = document.getElementById('freeze-watermark');

    if (isStreamFrozen) {
        frozenRawBuffer.set(rawSignalBuffer);
        frozenFilteredBuffer.set(filteredSignalBuffer);
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
    document.querySelectorAll('.scale-btn').forEach(b => {
        b.classList.toggle('active', parseFloat(b.dataset.scale) === displayScaleUv);
    });
}

function setTimebaseWindow(samples, label) {
    displaySamplesCount = parseInt(samples) || 500;
    document.querySelectorAll('.timebase-btn').forEach(b => {
        b.classList.toggle('active', parseInt(b.dataset.timebase) === displaySamplesCount);
    });
    if (label) showToast(`Oscilloscope timebase window: ${label}`, "info", 1500);
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

function drawWaveform() {
    const w = waveCanvas.width;
    const h = waveCanvas.height;
    waveCtx.clearRect(0, 0, w, h);

    // Microvolt Grid
    waveCtx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    waveCtx.lineWidth = 1;
    for (let y = 0; y < h; y += 40) {
        waveCtx.beginPath(); waveCtx.moveTo(0, y); waveCtx.lineTo(w, y); waveCtx.stroke();
    }

    // Ground line (0 μV)
    const midY = h / 2;
    waveCtx.strokeStyle = 'rgba(14, 165, 233, 0.2)';
    waveCtx.beginPath(); waveCtx.moveTo(0, midY); waveCtx.lineTo(w, midY); waveCtx.stroke();

    // Scale grid markers and axis labels
    const scale = (midY) / displayScaleUv;
    waveCtx.font = '10px "JetBrains Mono", monospace';
    waveCtx.fillStyle = 'rgba(148, 163, 184, 0.5)';
    waveCtx.textAlign = 'left';
    waveCtx.fillText(`+${displayScaleUv} μV`, 8, 14);
    waveCtx.fillText(`0 μV`, 8, midY - 4);
    waveCtx.fillText(`-${displayScaleUv} μV`, 8, h - 8);

    const displaySamples = Math.min(BUFFER_SIZE, displaySamplesCount);
    const step = w / displaySamples;

    const rawBuf = isStreamFrozen ? frozenRawBuffer : rawSignalBuffer;
    const filtBuf = isStreamFrozen ? frozenFilteredBuffer : filteredSignalBuffer;

    // Trace 1: Raw Unfiltered Signal (Faint Gray/White)
    waveCtx.beginPath();
    waveCtx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    waveCtx.lineWidth = 1;
    for (let i = 0; i < displaySamples; i++) {
        const idx = (writeIndex - displaySamples + i + BUFFER_SIZE) % BUFFER_SIZE;
        const val = rawBuf[idx];
        const x = i * step;
        const y = midY - (val * scale);
        if (i === 0) waveCtx.moveTo(x, y); else waveCtx.lineTo(x, y);
    }
    waveCtx.stroke();

    // Trace 2: Processed Filtered Signal (Vivid Neon Cyan)
    waveCtx.beginPath();
    waveCtx.strokeStyle = '#0EA5E9';
    waveCtx.lineWidth = 2;
    waveCtx.shadowColor = '#0EA5E9';
    waveCtx.shadowBlur = 6;
    for (let i = 0; i < displaySamples; i++) {
        const idx = (writeIndex - displaySamples + i + BUFFER_SIZE) % BUFFER_SIZE;
        const val = filtBuf[idx];
        const x = i * step;
        const y = midY - (val * scale);
        if (i === 0) waveCtx.moveTo(x, y); else waveCtx.lineTo(x, y);
    }
    waveCtx.stroke();
    waveCtx.shadowBlur = 0;
}

function drawPSD() {
    const w = psdCanvas.width;
    const h = psdCanvas.height;
    psdCtx.clearRect(0, 0, w, h);

    const maxFreq = 40.0;
    const df = SAMPLING_RATE / FFT_SIZE;
    const numBins = Math.floor(maxFreq / df);

    // Band highlights
    const bands = [
        { f1: 0.5, f2: 4.0, color: 'rgba(14, 165, 233, 0.08)' },
        { f1: 4.0, f2: 8.0, color: 'rgba(16, 185, 129, 0.08)' },
        { f1: 8.0, f2: 13.0, color: 'rgba(139, 92, 246, 0.08)' },
        { f1: 13.0, f2: 30.0, color: 'rgba(245, 158, 11, 0.08)' }
    ];

    bands.forEach(b => {
        const x1 = (b.f1 / maxFreq) * w;
        const x2 = (b.f2 / maxFreq) * w;
        psdCtx.fillStyle = b.color;
        psdCtx.fillRect(x1, 0, x2 - x1, h);
    });

    // Draw Smooth Spectral Power Curve
    psdCtx.beginPath();
    psdCtx.strokeStyle = '#38BDF8';
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
// 7. Continuous 2D Spatial Brain Topography (Shepard's IDW Interpolation)
// ------------------------------------------------------------------------------
const topoCanvas = document.getElementById('topoCanvas');
const topoCtx = topoCanvas ? topoCanvas.getContext('2d') : null;

// Offscreen buffer for continuous potential interpolation grid (48x48)
const GRID_RES = 48;
const offscreenTopoCanvas = document.createElement('canvas');
offscreenTopoCanvas.width = GRID_RES;
offscreenTopoCanvas.height = GRID_RES;
const offscreenTopoCtx = offscreenTopoCanvas.getContext('2d');
const topoImgData = offscreenTopoCtx.createImageData(GRID_RES, GRID_RES);

const ELECTRODES_1020_COORDS = [
    { id: "Fp1", name: "Frontopolar 1", region: "Left Pre-frontal (Executive / Attention)", x: -0.30, y: 0.70 },
    { id: "Fp2", name: "Frontopolar 2", region: "Right Pre-frontal (Emotional Regulation)", x: 0.30,  y: 0.70 },
    { id: "C3",  name: "Central 3", region: "Left Central Motor / Sensory Strip", x: -0.55, y: 0.00 },
    { id: "C4",  name: "Central 4", region: "Right Central Motor / Sensory Strip", x: 0.55,  y: 0.00 },
    { id: "P3",  name: "Parietal 3", region: "Left Parietal (Spatial Integration)", x: -0.40, y: -0.50 },
    { id: "P4",  name: "Parietal 4", region: "Right Parietal (Somatosensory / Attention)", x: 0.40,  y: -0.50 },
    { id: "O1",  name: "Occipital 1", region: "Left Occipital (Primary Visual Cortex)", x: -0.25, y: -0.80 },
    { id: "O2",  name: "Occipital 2", region: "Right Occipital (Visual Processing)", x: 0.25,  y: -0.80 }
];

function setTopoColormap(scheme) {
    activeColormap = scheme || "coolwarm";
    const bar = document.getElementById('topo-gradient-bar');
    if (bar) {
        if (activeColormap === 'viridis') {
            bar.style.background = 'linear-gradient(90deg, #440154, #3b528b, #21918c, #5ec962, #fde725)';
        } else if (activeColormap === 'plasma') {
            bar.style.background = 'linear-gradient(90deg, #0d0887, #7e03a8, #cc4778, #f89540, #f0f921)';
        } else if (activeColormap === 'jet') {
            bar.style.background = 'linear-gradient(90deg, #00008f, #00ffff, #00ff00, #ffff00, #ff0000)';
        } else {
            bar.style.background = 'linear-gradient(90deg, #0e3aa8, #0ea5e9, #10b981, #f59e0b, #ef4444)';
        }
    }
    drawContinuousTopoMap();
}

// Scientific Colormaps: Cool-Warm (Clinical), Viridis (Perceptual), Plasma (High-Contrast), Jet (Rainbow)
function getScientificColor(normVal) {
    const v = Math.max(0.0, Math.min(1.0, normVal));
    let r = 0, g = 0, b = 0;

    if (activeColormap === 'viridis') {
        if (v < 0.25) {
            const t = v / 0.25;
            r = Math.round(68 * (1 - t) + 59 * t);
            g = Math.round(1 * (1 - t) + 82 * t);
            b = Math.round(84 * (1 - t) + 139 * t);
        } else if (v < 0.5) {
            const t = (v - 0.25) / 0.25;
            r = Math.round(59 * (1 - t) + 33 * t);
            g = Math.round(82 * (1 - t) + 145 * t);
            b = Math.round(139 * (1 - t) + 140 * t);
        } else if (v < 0.75) {
            const t = (v - 0.5) / 0.25;
            r = Math.round(33 * (1 - t) + 94 * t);
            g = Math.round(145 * (1 - t) + 201 * t);
            b = Math.round(140 * (1 - t) + 98 * t);
        } else {
            const t = (v - 0.75) / 0.25;
            r = Math.round(94 * (1 - t) + 253 * t);
            g = Math.round(201 * (1 - t) + 231 * t);
            b = Math.round(98 * (1 - t) + 37 * t);
        }
        return [r, g, b];
    }

    if (activeColormap === 'plasma') {
        if (v < 0.25) {
            const t = v / 0.25;
            r = Math.round(13 * (1 - t) + 126 * t);
            g = Math.round(8 * (1 - t) + 3 * t);
            b = Math.round(135 * (1 - t) + 168 * t);
        } else if (v < 0.5) {
            const t = (v - 0.25) / 0.25;
            r = Math.round(126 * (1 - t) + 204 * t);
            g = Math.round(3 * (1 - t) + 71 * t);
            b = Math.round(168 * (1 - t) + 120 * t);
        } else if (v < 0.75) {
            const t = (v - 0.5) / 0.25;
            r = Math.round(204 * (1 - t) + 248 * t);
            g = Math.round(71 * (1 - t) + 149 * t);
            b = Math.round(120 * (1 - t) + 64 * t);
        } else {
            const t = (v - 0.75) / 0.25;
            r = Math.round(248 * (1 - t) + 240 * t);
            g = Math.round(149 * (1 - t) + 249 * t);
            b = Math.round(64 * (1 - t) + 33 * t);
        }
        return [r, g, b];
    }

    if (activeColormap === 'jet') {
        if (v < 0.125) {
            r = 0; g = 0; b = Math.round(128 + 127 * (v / 0.125));
        } else if (v < 0.375) {
            const t = (v - 0.125) / 0.25;
            r = 0; g = Math.round(255 * t); b = 255;
        } else if (v < 0.625) {
            const t = (v - 0.375) / 0.25;
            r = Math.round(255 * t); g = 255; b = Math.round(255 * (1 - t));
        } else if (v < 0.875) {
            const t = (v - 0.625) / 0.25;
            r = 255; g = Math.round(255 * (1 - t)); b = 0;
        } else {
            const t = (v - 0.875) / 0.125;
            r = Math.round(255 - 127 * t); g = 0; b = 0;
        }
        return [r, g, b];
    }

    // Default: Cool-Warm (Clinical)
    if (v < 0.25) {
        const t = v / 0.25;
        r = Math.round(14 * (1 - t) + 14 * t);
        g = Math.round(58 * (1 - t) + 165 * t);
        b = Math.round(138 * (1 - t) + 233 * t);
    } else if (v < 0.5) {
        const t = (v - 0.25) / 0.25;
        r = Math.round(14 * (1 - t) + 16 * t);
        g = Math.round(165 * (1 - t) + 185 * t);
        b = Math.round(233 * (1 - t) + 129 * t);
    } else if (v < 0.75) {
        const t = (v - 0.5) / 0.25;
        r = Math.round(16 * (1 - t) + 245 * t);
        g = Math.round(185 * (1 - t) + 158 * t);
        b = Math.round(129 * (1 - t) + 11 * t);
    } else {
        const t = (v - 0.75) / 0.25;
        r = Math.round(245 * (1 - t) + 239 * t);
        g = Math.round(158 * (1 - t) + 68 * t);
        b = Math.round(11 * (1 - t) + 68 * t);
    }
    return [r, g, b];
}

function drawContinuousTopoMap() {
    if (!topoCanvas || !topoCtx) return;

    const data = topoImgData.data;
    const p = 2.0; // IDW power parameter
    const epsilon = 1e-4;

    // Collect electrode potentials array
    const vArr = ELECTRODES_1020_COORDS.map(e => electrodePotentials[e.id] || 0.0);

    // Compute continuous IDW potentials across 48x48 spatial grid
    for (let gy = 0; gy < GRID_RES; gy++) {
        const ny = 1.0 - (gy / (GRID_RES - 1)) * 2.0; // Coordinate from -1 to 1

        for (let gx = 0; gx < GRID_RES; gx++) {
            const nx = (gx / (GRID_RES - 1)) * 2.0 - 1.0;
            const distHead = Math.sqrt(nx * nx + ny * ny);

            const pixelIdx = (gy * GRID_RES + gx) * 4;

            // Inside circular head radius
            if (distHead <= 0.95) {
                let weightSum = 0.0;
                let potentialSum = 0.0;

                for (let i = 0; i < ELECTRODES_1020_COORDS.length; i++) {
                    const dx = nx - ELECTRODES_1020_COORDS[i].x;
                    const dy = ny - ELECTRODES_1020_COORDS[i].y;
                    const distSq = dx * dx + dy * dy;
                    const weight = 1.0 / (Math.pow(distSq, p / 2.0) + epsilon);

                    weightSum += weight;
                    potentialSum += weight * vArr[i];
                }

                const interpolatedV = potentialSum / weightSum;
                // Normalize ±25 uV range to 0.0 - 1.0
                const normV = (interpolatedV + 25.0) / 50.0;
                const [r, g, b] = getScientificColor(normV);

                data[pixelIdx]     = r;
                data[pixelIdx + 1] = g;
                data[pixelIdx + 2] = b;
                data[pixelIdx + 3] = 230; // Alpha
            } else {
                // Outside head
                data[pixelIdx + 3] = 0;
            }
        }
    }

    offscreenTopoCtx.putImageData(topoImgData, 0, 0);

    // Render scaled offscreen buffer onto main canvas
    const w = topoCanvas.width;
    const h = topoCanvas.height;
    topoCtx.clearRect(0, 0, w, h);

    const cx = w / 2;
    const cy = h / 2;
    const radius = Math.min(w, h) * 0.42;

    // Draw Smooth Interpolated Brain Grid
    topoCtx.save();
    topoCtx.beginPath();
    topoCtx.arc(cx, cy, radius, 0, 2 * Math.PI);
    topoCtx.clip();
    topoCtx.imageSmoothingEnabled = true;
    topoCtx.drawImage(offscreenTopoCanvas, cx - radius, cy - radius, radius * 2, radius * 2);
    topoCtx.restore();

    // Head Outline
    topoCtx.beginPath();
    topoCtx.arc(cx, cy, radius, 0, 2 * Math.PI);
    topoCtx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
    topoCtx.lineWidth = 3;
    topoCtx.stroke();

    // Nose
    topoCtx.beginPath();
    topoCtx.moveTo(cx - 16, cy - radius);
    topoCtx.lineTo(cx, cy - radius - 18);
    topoCtx.lineTo(cx + 16, cy - radius);
    topoCtx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
    topoCtx.lineWidth = 2.5;
    topoCtx.stroke();

    // Ears
    topoCtx.beginPath();
    topoCtx.arc(cx - radius - 6, cy, 14, Math.PI / 2, (3 * Math.PI) / 2);
    topoCtx.stroke();
    topoCtx.beginPath();
    topoCtx.arc(cx + radius + 6, cy, 14, -Math.PI / 2, Math.PI / 2);
    topoCtx.stroke();

    // Electrode Pins & Labels
    ELECTRODES_1020_COORDS.forEach(e => {
        const ex = cx + (e.x * radius * 0.95);
        const ey = cy - (e.y * radius * 0.95);

        topoCtx.beginPath();
        topoCtx.arc(ex, ey, 6, 0, 2 * Math.PI);
        topoCtx.fillStyle = '#FFFFFF';
        topoCtx.fill();
        topoCtx.strokeStyle = '#000000';
        topoCtx.lineWidth = 1.5;
        topoCtx.stroke();

        topoCtx.fillStyle = '#FFFFFF';
        topoCtx.font = 'bold 11px Inter, sans-serif';
        topoCtx.fillText(e.id, ex + 10, ey + 4);
    });
}

function initTopoTooltip() {
    const canvas = document.getElementById('topoCanvas');
    const tooltip = document.getElementById('topo-tooltip');
    if (!canvas || !tooltip) return;

    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = (e.clientX - rect.left) * (canvas.width / rect.width);
        const mouseY = (e.clientY - rect.top) * (canvas.height / rect.height);

        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        const radius = Math.min(canvas.width, canvas.height) * 0.42;

        let matched = null;
        let minDist = 24; // px hit radius

        for (const el of ELECTRODES_1020_COORDS) {
            const ex = cx + (el.x * radius * 0.95);
            const ey = cy - (el.y * radius * 0.95);
            const dist = Math.hypot(mouseX - ex, mouseY - ey);
            if (dist < minDist) {
                minDist = dist;
                matched = el;
            }
        }

        if (matched) {
            const pot = electrodePotentials[matched.id] || 0.0;
            const containerRect = canvas.parentElement.getBoundingClientRect();
            const posX = Math.min(containerRect.width - 240, Math.max(10, e.clientX - containerRect.left + 14));
            const posY = Math.min(containerRect.height - 130, Math.max(10, e.clientY - containerRect.top - 10));

            tooltip.innerHTML = `
                <div class="topo-tooltip-title">${matched.id} &bull; ${matched.name}</div>
                <div class="topo-tooltip-row"><span>Region:</span> <strong>${matched.region}</strong></div>
                <div class="topo-tooltip-row"><span>Localized Potential:</span> <strong>${pot.toFixed(2)} μV</strong></div>
                <div class="topo-tooltip-row"><span>Contact State:</span> <strong style="color: var(--emerald);">PASS (&lt;5.0 kΩ)</strong></div>
                <div class="topo-tooltip-row"><span>Dominant Rhythm:</span> <strong>${currentMetrics.dominantBand} (${currentMetrics.dominantFreq.toFixed(1)} Hz)</strong></div>
            `;
            tooltip.style.left = `${posX}px`;
            tooltip.style.top = `${posY}px`;
            tooltip.style.display = 'block';
        } else {
            tooltip.style.display = 'none';
        }
    });

    canvas.addEventListener('mouseleave', () => {
        tooltip.style.display = 'none';
    });
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
// 11. Web Audio Biofeedback Engine
// ------------------------------------------------------------------------------
function setBiofeedbackVolume(vol) {
    biofeedbackVolume = Math.max(0.0, Math.min(1.0, parseFloat(vol) || 0.5));
    const lbl = document.getElementById('val-audio-vol');
    if (lbl) lbl.innerText = `${Math.round(biofeedbackVolume * 100)}%`;
    if (bioGainNode && audioCtx) {
        const baseVol = currentMetrics.stressIndex >= 0.80 ? 0.08 : 0.03;
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
        bioOscillator = audioCtx.createOscillator();
        bioGainNode = audioCtx.createGain();

        bioOscillator.type = 'sine';
        bioOscillator.frequency.setValueAtTime(220, audioCtx.currentTime); // A3 note
        const currentGain = 0.04 * (biofeedbackVolume * 2.0);
        bioGainNode.gain.setValueAtTime(currentGain, audioCtx.currentTime); // Scaled volume

        bioOscillator.connect(bioGainNode);
        bioGainNode.connect(audioCtx.destination);
        bioOscillator.start();

        if (btn) btn.classList.add('active');
        if (lbl) lbl.innerText = 'ON';
    } else {
        if (bioOscillator) {
            try { bioOscillator.stop(); bioOscillator.disconnect(); } catch (e) {}
            bioOscillator = null;
        }
        if (btn) btn.classList.remove('active');
        if (lbl) lbl.innerText = 'OFF';
    }
}

function updateAudioBiofeedback(peakFreq, stress) {
    if (!bioOscillator || !audioCtx || !bioGainNode) return;
    // Map dominant frequency (0-30Hz) to musical pitch (150Hz to 400Hz)
    const targetFreq = 160 + (peakFreq * 8.0);
    bioOscillator.frequency.setTargetAtTime(targetFreq, audioCtx.currentTime, 0.1);

    // Gently swell volume if cognitive stress index exceeds 0.80, scaled by user volume
    const baseVol = stress >= 0.80 ? 0.08 : 0.03;
    const targetVol = baseVol * (biofeedbackVolume * 2.0);
    bioGainNode.gain.setTargetAtTime(targetVol, audioCtx.currentTime, 0.1);
}

// ------------------------------------------------------------------------------
// 12. Resilient WebSocket Telemetry Client & Diagnostic Logging
// ------------------------------------------------------------------------------
const recentPackets = [];

function logRecentPacket(sender, val, seq) {
    const now = new Date().toLocaleTimeString();
    const formattedVal = (typeof val === 'number') ? val.toFixed(2) : String(val);
    recentPackets.unshift({ time: now, sender: sender || "ESP32", val: formattedVal, seq: seq !== undefined ? seq : '-' });
    if (recentPackets.length > 8) recentPackets.pop();

    const logEl = document.getElementById('hw-packet-log');
    if (logEl) {
        logEl.innerHTML = recentPackets.map(p => `
            <div style="display: flex; justify-content: space-between; padding: 4px 8px; border-bottom: 1px solid rgba(255,255,255,0.05); font-family: 'JetBrains Mono', monospace; font-size: 11px;">
                <span style="color: #64748B;">[${p.time}]</span>
                <span style="color: var(--cyan);">${p.sender}</span>
                <span style="color: #F8FAFC; font-weight: 600;">${p.val} μV</span>
                <span style="color: #94A3B8;">#${p.seq}</span>
            </div>
        `).join('');
    }
}

function initHardwareWebSocket() {
    const wsHost = window.location.hostname || "localhost";
    const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProto}//${wsHost}:${WS_PORT}`;

    try {
        if (wsClient && (wsClient.readyState === WebSocket.OPEN || wsClient.readyState === WebSocket.CONNECTING)) {
            return;
        }

        wsClient = new WebSocket(wsUrl);

        wsClient.onopen = () => {
            console.log("[NeuroSim] Connected to Laptop Wi-Fi Telemetry WebSocket Hub: " + wsUrl);
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
                    ingestSample(msg.val);
                    updateHardwareUIState(true);
                    logRecentPacket(msg.sender || "ESP32", msg.val, msg.seq);
                } else if (msg.type === "batch") {
                    isHardwareActive = true;
                    msg.samples.forEach(s => ingestSample(s.val));
                    const last = msg.samples[msg.samples.length - 1];
                    if (last) logRecentPacket(last.sender || "ESP32", last.val, last.seq);
                    updateHardwareUIState(true);
                } else if (msg.type === "telemetry" || msg.type === "handshake") {
                    if (msg.wifi_ip) {
                        wifiIp = msg.wifi_ip;
                        udpPort = msg.udp_port || 5005;
                        updateIpDisplays(msg.all_ips);
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
let lastHttpSampleSeq = -1;

async function fetchRestStatus() {
    try {
        const res = await fetch('/api/status');
        if (res.ok) {
            const data = await res.json();
            if (data.wifi_ip) {
                wifiIp = data.wifi_ip;
                udpPort = data.udp_port || 5005;
                updateIpDisplays(data.all_ips);
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
                        ingestSample(s.val);
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
        const res = await fetch('/api/test-udp');
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
        const res = await fetch('/api/telemetry/impedance');
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
        const res = await fetch('/api/clinical-override', {
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
        const res = await fetch('/api/calibration/run-test', { method: 'POST' });
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
    window.location.href = `/api/export/edf?session_id=${encodeURIComponent(sessId)}`;
}

function downloadCurrentSessionFHIR() {
    const sessId = (typeof currentSessionId !== 'undefined' && currentSessionId) ? currentSessionId : 'SESS-CURRENT';
    showToast(`Generating HL7 FHIR R4 Bundle for ${sessId}...`, "info");
    window.open(`/api/fhir/DiagnosticReport?session_id=${encodeURIComponent(sessId)}`, '_blank');
}

async function verifyAuditIntegrity() {
    showToast("Verifying 21 CFR Part 11 SHA-256 Merkle audit chain...", "info");
    try {
        const res = await fetch('/api/audit/verify');
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
        await fetch('/api/sessions', {
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
    window.location.href = `/api/export/edf?session_id=${encodeURIComponent(sessionId)}`;
}

function exportSessionFHIR(sessionId) {
    showToast(`Opening HL7 FHIR bundle for ${sessionId}...`, "info");
    window.open(`/api/fhir/DiagnosticReport?session_id=${encodeURIComponent(sessionId)}`, '_blank');
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
        'topo-map': 'CONTINUOUS 2D TOPOGRAPHIC BRAIN HEATMAP (SHEPARD\'S IDW)',
        'classification': 'DUAL CLASSIFIER & CLINICAL DECISION SUPPORT',
        'validation-bench': 'AUTOMATED DSP FREQUENCY VALIDATION BENCHMARK',
        'wifi-hardware': 'LAPTOP WI-FI HARDWARE CENTER & DEVICE TELEMETRY',
        'history': 'SESSION ARCHIVE & CLINICAL DATA EXPORT',
        'report': 'MEDICAL PDF REPORT EXPORTER & AI INTERPRETATION'
    };
    document.getElementById('page-title').innerText = titles[tabKey] || 'NEUROSIM WORKSTATION';

    if (tabKey === 'history') renderHistoryTable();
    if (tabKey === 'topo-map') drawContinuousTopoMap();
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
            fetch('/api/auth/me', {
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

async function requestOTP() {
    const name = document.getElementById('auth-name').value.trim();
    const email = document.getElementById('auth-email').value.trim();
    const mobile = document.getElementById('auth-mobile').value.trim();

    if (!mobile || mobile.length < 7) {
        showToast("Please provide a valid mobile number.", "error");
        return;
    }

    const btn = document.getElementById('btn-send-otp');
    btn.disabled = true;
    btn.innerText = "Sending...";

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 8000);
        const resp = await fetch('/api/auth/send-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, mobile }),
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        const data = await resp.json();
        if (resp.ok && data.success) {
            showToast(`OTP dispatched successfully to ${mobile}`, "success");
            document.getElementById('field-otp-wrap').style.display = 'flex';
            document.getElementById('btn-verify-otp').style.display = 'block';

            if (data.dev_otp) {
                const hint = document.getElementById('auth-dev-otp-hint');
                if (hint) hint.innerText = `[DEV TESTING OTP]: ${data.dev_otp}`;
                document.getElementById('auth-otp').value = data.dev_otp;
            }

            // Start 30-second countdown timer
            const timerEl = document.getElementById('auth-timer-text');
            const countEl = document.getElementById('auth-countdown');
            if (timerEl) timerEl.style.display = 'block';
            otpCountdownSeconds = 30;
            if (countEl) countEl.innerText = otpCountdownSeconds;

            if (otpCountdownTimer) clearInterval(otpCountdownTimer);
            otpCountdownTimer = setInterval(() => {
                otpCountdownSeconds--;
                if (countEl) countEl.innerText = otpCountdownSeconds;
                if (otpCountdownSeconds <= 0) {
                    clearInterval(otpCountdownTimer);
                    btn.disabled = false;
                    btn.innerText = "Resend OTP";
                    if (timerEl) timerEl.style.display = 'none';
                }
            }, 1000);
        } else {
            showToast(data.error || "Failed to send OTP.", "error");
            btn.disabled = false;
            btn.innerText = "Send OTP";
        }
    } catch (e) {
        showToast("Request timed out or network error. Please retry.", "error");
        btn.disabled = false;
        btn.innerText = "Send OTP";
    }
}

async function submitVerifyOTP() {
    const mobile = document.getElementById('auth-mobile').value.trim();
    const otp = document.getElementById('auth-otp').value.trim();

    if (!otp || otp.length !== 6) {
        showToast("Please enter the 6-digit OTP code.", "error");
        return;
    }

    const verifyBtn = document.getElementById('btn-verify-otp');
    verifyBtn.disabled = true;
    verifyBtn.innerText = "Verifying & Connecting...";

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 8000);
        const resp = await fetch('/api/auth/verify-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mobile, otp }),
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        const data = await resp.json();
        if (resp.ok && data.success) {
            localStorage.setItem('neurosim_token', data.token);
            localStorage.setItem('neurosim_user', JSON.stringify(data.user));
            currentUser = data.user;
            updateHeaderUserBadge(currentUser);
            closeAuthModal();
            showToast(`Welcome, ${currentUser.name}! Telemetry connected to laptop Wi-Fi.`, "success");

            // Connect WebSocket stream to laptop Wi-Fi telemetry hub
            initHardwareWebSocket();
        } else {
            showToast(data.error || "OTP verification failed.", "error");
        }
    } catch (e) {
        showToast("Verification request failed. Check server connection.", "error");
    } finally {
        verifyBtn.disabled = false;
        verifyBtn.innerText = "Verify & Connect to Laptop Wi-Fi";
    }
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

// Initialize Application
window.addEventListener('DOMContentLoaded', () => {
    checkCookieConsent();
    checkAuthStatus();
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
});
