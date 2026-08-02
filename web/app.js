// NeuroSim Web Application Core Logic & DSP Engine

let simParams = { delta: 0.3, theta: 0.4, alpha: 0.8, beta: 0.3, noise: 0.15 };
let tCursor = 0.0;
let isRecording = false;
let recordingStart = 0;
let sampleCount = 0;
let currentSessionData = null;

// Hardware Serial API state
let serialPort = null;
let serialReader = null;
let isHardwareConnected = false;

function updateSim() {
    simParams.delta = parseFloat(document.getElementById('sld-delta').value) / 100.0;
    simParams.theta = parseFloat(document.getElementById('sld-theta').value) / 100.0;
    simParams.alpha = parseFloat(document.getElementById('sld-alpha').value) / 100.0;
    simParams.beta = parseFloat(document.getElementById('sld-beta').value) / 100.0;
    simParams.noise = parseFloat(document.getElementById('sld-noise').value) / 100.0;
}

function switchTab(tabKey) {
    document.querySelectorAll('.view-screen').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.getElementById('screen-' + tabKey).classList.add('active');
    event.currentTarget.classList.add('active');
    
    if (tabKey === 'history') {
        renderHistoryTable();
    }
}

// Canvases
const waveCanvas = document.getElementById('waveCanvas');
const waveCtx = waveCanvas.getContext('2d');
const psdCanvas = document.getElementById('psdCanvas');
const psdCtx = psdCanvas.getContext('2d');

function resizeCanvases() {
    if (waveCanvas && psdCanvas) {
        waveCanvas.width = waveCanvas.clientWidth;
        waveCanvas.height = waveCanvas.clientHeight;
        psdCanvas.width = psdCanvas.clientWidth;
        psdCanvas.height = psdCanvas.clientHeight;
    }
}
window.addEventListener('resize', resizeCanvases);
setTimeout(resizeCanvases, 100);

let waveHistory = new Array(350).fill(0);

// Main Animation Loop
function renderLoop() {
    tCursor += 0.04;

    // Signal generation
    let val = 0;
    if (!isHardwareConnected) {
        const sD = simParams.delta * Math.sin(2 * Math.PI * 2 * tCursor);
        const sT = simParams.theta * Math.sin(2 * Math.PI * 6 * tCursor);
        const sA = simParams.alpha * Math.sin(2 * Math.PI * 10 * tCursor);
        const sB = simParams.beta * Math.sin(2 * Math.PI * 20 * tCursor);
        const n = (Math.random() - 0.5) * simParams.noise * 2;
        val = (sD + sT + sA + sB + n) * 32.0;
    } else {
        val = waveHistory[waveHistory.length - 1];
    }

    waveHistory.shift();
    waveHistory.push(val);

    // Draw Waveform
    const w = waveCanvas.width;
    const h = waveCanvas.height;
    waveCtx.clearRect(0, 0, w, h);
    
    // Grid lines
    waveCtx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    waveCtx.lineWidth = 1;
    for (let y = 0; y < h; y += 30) {
        waveCtx.beginPath(); waveCtx.moveTo(0, y); waveCtx.lineTo(w, y); waveCtx.stroke();
    }

    waveCtx.beginPath();
    waveCtx.strokeStyle = '#06B6D4';
    waveCtx.lineWidth = 2;
    waveCtx.shadowColor = '#06B6D4';
    waveCtx.shadowBlur = 8;

    const step = w / waveHistory.length;
    for (let i = 0; i < waveHistory.length; i++) {
        const x = i * step;
        const y = h / 2 - waveHistory[i];
        if (i === 0) waveCtx.moveTo(x, y);
        else waveCtx.lineTo(x, y);
    }
    waveCtx.stroke();
    waveCtx.shadowBlur = 0;

    // Calculate Band Powers
    const total = simParams.delta + simParams.theta + simParams.alpha + simParams.beta + 0.001;
    const pD = ((simParams.delta / total) * 100).toFixed(1);
    const pT = ((simParams.theta / total) * 100).toFixed(1);
    const pA = ((simParams.alpha / total) * 100).toFixed(1);
    const pB = ((simParams.beta / total) * 100).toFixed(1);

    document.getElementById('lbl-delta').innerText = pD + ' %';
    document.getElementById('fill-delta').style.width = pD + '%';
    document.getElementById('lbl-theta').innerText = pT + ' %';
    document.getElementById('fill-theta').style.width = pT + '%';
    document.getElementById('lbl-alpha').innerText = pA + ' %';
    document.getElementById('fill-alpha').style.width = pA + '%';
    document.getElementById('lbl-beta').innerText = pB + ' %';
    document.getElementById('fill-beta').style.width = pB + '%';

    // Stress & Metrics
    const stress = (simParams.beta / (simParams.alpha + simParams.theta + 0.001)).toFixed(2);
    document.getElementById('m-stress').innerText = stress;
    
    const tbr = (simParams.theta / (simParams.beta + 0.001)).toFixed(2);
    const abr = (simParams.alpha / (simParams.beta + 0.001)).toFixed(2);
    const eng = (simParams.beta / (simParams.alpha + simParams.theta + 0.001)).toFixed(2);
    
    if (document.getElementById('b-tbr')) {
        document.getElementById('b-tbr').innerText = tbr;
        document.getElementById('b-abr').innerText = abr;
        document.getElementById('b-eng').innerText = eng;
    }

    // Cognitive State Logic
    let state = 'MODERATE';
    if (parseFloat(pB) >= 35 || stress >= 0.8) {
        state = 'HIGH';
        document.getElementById('m-load').style.color = '#EF4444';
    } else if (parseFloat(pA) >= 35) {
        state = 'RELAXED';
        document.getElementById('m-load').style.color = '#8B5CF6';
    } else {
        state = 'MODERATE';
        document.getElementById('m-load').style.color = '#06B6D4';
    }
    document.getElementById('m-load').innerText = state;

    // Draw PSD Spectrum
    const pw = psdCanvas.width;
    const ph = psdCanvas.height;
    psdCtx.clearRect(0, 0, pw, ph);

    const bands = [
        { f: 2, val: pD, color: '#06B6D4' },
        { f: 6, val: pT, color: '#10B981' },
        { f: 10, val: pA, color: '#8B5CF6' },
        { f: 20, val: pB, color: '#F59E0B' }
    ];

    bands.forEach(b => {
        const x = (b.f / 40) * pw;
        const barH = (parseFloat(b.val) / 100) * (ph - 40);
        psdCtx.fillStyle = b.color;
        psdCtx.fillRect(x - 12, ph - barH - 20, 24, barH);
        psdCtx.fillStyle = '#94A3B8';
        psdCtx.font = '10px Segoe UI';
        psdCtx.fillText(b.f + 'Hz', x - 10, ph - 5);
    });

    if (isRecording) {
        sampleCount += 10;
        const elapsed = Math.floor((Date.now() - recordingStart) / 1000);
        const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const secs = String(elapsed % 60).padStart(2, '0');
        document.getElementById('s-dur').innerText = `${mins}:${secs}`;
        document.getElementById('s-samples').innerText = sampleCount;
    }

    requestAnimationFrame(renderLoop);
}

renderLoop();

// Session Controls
function startSession() {
    isRecording = true;
    recordingStart = Date.now();
    sampleCount = 0;
    const id = 'SESS-' + Math.floor(1000 + Math.random() * 9000);
    document.getElementById('s-id').innerText = id;
}

function stopSession() {
    if (!isRecording) return;
    isRecording = false;

    const elapsed = Math.floor((Date.now() - recordingStart) / 1000);
    const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const secs = String(elapsed % 60).padStart(2, '0');

    currentSessionData = {
        id: document.getElementById('s-id').innerText,
        duration: `${mins}:${secs}`,
        samples: sampleCount,
        load: document.getElementById('m-load').innerText,
        stress: document.getElementById('m-stress').innerText,
        delta: document.getElementById('fill-delta').style.width.replace('%', ''),
        theta: document.getElementById('fill-theta').style.width.replace('%', ''),
        alpha: document.getElementById('fill-alpha').style.width.replace('%', ''),
        beta: document.getElementById('fill-beta').style.width.replace('%', ''),
        date: new Date().toLocaleString()
    };

    saveSessionLocal(currentSessionData);
    alert('Session Recorded & Saved to Local History!');
}

function downloadCurrentReport() {
    if (!currentSessionData) {
        stopSession();
    }
    exportSessionPDF(currentSessionData);
}

function saveSessionLocal(session) {
    let history = JSON.parse(localStorage.getItem('neurosim_history') || '[]');
    history.unshift(session);
    localStorage.setItem('neurosim_history', JSON.stringify(history));
}

function renderHistoryTable() {
    const history = JSON.parse(localStorage.getItem('neurosim_history') || '[]');
    const container = document.getElementById('history-table-body');
    if (!container) return;

    if (history.length === 0) {
        container.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#94A3B8;">No recorded sessions found.</td></tr>';
        return;
    }

    container.innerHTML = history.map(item => `
        <tr>
            <td><strong>${item.id}</strong></td>
            <td>${item.date}</td>
            <td>${item.duration}</td>
            <td><span style="color:${item.load === 'HIGH' ? '#EF4444' : '#06B6D4'}; font-weight:700;">${item.load}</span></td>
            <td>${item.stress}</td>
            <td><button class="btn" style="padding:4px 10px; font-size:11px;" onclick='exportSessionPDF(${JSON.stringify(item)})'>📄 PDF</button></td>
        </tr>
    `).join('');
}

// Hardware Web Serial Connect
async function connectESP32Serial() {
    if (!('serial' in navigator)) {
        alert('Web Serial API is not supported on this browser. Please use Google Chrome or MS Edge.');
        return;
    }
    try {
        serialPort = await navigator.serial.requestPort();
        await serialPort.open({ baudRate: 115200 });
        isHardwareConnected = true;
        document.getElementById('mode-badge').innerText = 'HARDWARE MODE (ESP32)';
        document.getElementById('mode-badge').style.borderColor = '#10B981';
        document.getElementById('mode-badge').style.color = '#10B981';
        alert('ESP32 Serial Port Connected Successfully!');
    } catch (e) {
        console.error('Serial Connection Failed:', e);
    }
}
