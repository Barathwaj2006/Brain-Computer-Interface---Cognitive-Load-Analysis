// Browser renderer for the authoritative RuntimeController API. No client-side EEG or DSP exists here.

let runtimeState = null;
let latestAnalysis = null;
let selectedWindowSeconds = 5;
let selectedChannel = "FP1";

const waveCanvas = document.getElementById("waveCanvas");
const psdCanvas = document.getElementById("psdCanvas");
const waveCtx = waveCanvas.getContext("2d");
const psdCtx = psdCanvas.getContext("2d");

async function api(path, options = {}) {
    const response = await fetch(path, options);
    const type = response.headers.get("content-type") || "";
    if (!response.ok) {
        const payload = type.includes("application/json") ? await response.json() : {};
        throw new Error(payload.error || `API request failed (${response.status})`);
    }
    return type.includes("application/json") ? response.json() : response;
}

function value(id, text) {
    const element = document.getElementById(id);
    if (element) element.innerText = text;
}

function metric(number, digits = 2, suffix = "") {
    return typeof number === "number" && Number.isFinite(number) ? `${number.toFixed(digits)}${suffix}` : "--";
}

function duration(seconds) {
    if (typeof seconds !== "number" || !Number.isFinite(seconds)) return "--";
    const total = Math.floor(seconds);
    return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}

function switchTab(tabKey) {
    document.querySelectorAll(".view-screen").forEach((element) => element.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach((element) => element.classList.remove("active"));
    document.getElementById(`screen-${tabKey}`).classList.add("active");
    if (window.event && window.event.currentTarget) window.event.currentTarget.classList.add("active");
    if (tabKey === "history") renderHistoryTable();
    if (tabKey === "research") loadResearchSummary();
    if (tabKey === "settings") renderSettings();
}

async function renderSettings() {
    const card = document.getElementById("settings-details");
    if (!card) return;
    try {
        const settings = await api("/api/settings");
        card.innerHTML = `
            <div style="display:grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-top: 12px; font-size:13px; color:#334155;">
                <div><strong>Application:</strong> ${settings.app_name} (${settings.version})</div>
                <div><strong>Sampling Rate:</strong> ${settings.sampling_rate} Hz</div>
                <div><strong>Window Duration:</strong> ${settings.window_size_sec} sec</div>
                <div><strong>Montage Channels:</strong> ${settings.channels.join(", ")}</div>
                <div><strong>Notch Filter:</strong> ${settings.filters.notch}</div>
                <div><strong>Ocular Filter:</strong> ${settings.filters.eog}</div>
                <div><strong>EMG Filter:</strong> ${settings.filters.emg}</div>
            </div>
        `;
    } catch (error) {
        card.innerHTML = `<p style="color:#EF4444;">Failed to load settings: ${error.message}</p>`;
    }
}

function resizeCanvases() {
    waveCanvas.width = waveCanvas.clientWidth;
    waveCanvas.height = waveCanvas.clientHeight;
    psdCanvas.width = psdCanvas.clientWidth;
    psdCanvas.height = psdCanvas.clientHeight;
}

function drawEmpty(context, canvas, message) {
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = "#94A3B8";
    context.font = "14px Segoe UI";
    context.textAlign = "center";
    context.fillText(message, canvas.width / 2, canvas.height / 2);
}

function drawWaveform(samples) {
    if (!samples || samples.length === 0) return drawEmpty(waveCtx, waveCanvas, "No Data Stream");
    const width = waveCanvas.width;
    const height = waveCanvas.height;
    const peak = Math.max(1, ...samples.map((sample) => Math.abs(sample)));
    waveCtx.clearRect(0, 0, width, height);
    waveCtx.beginPath();
    waveCtx.strokeStyle = "#06B6D4";
    waveCtx.lineWidth = 2;
    samples.forEach((sample, index) => {
        const x = (index / Math.max(samples.length - 1, 1)) * width;
        const y = height / 2 - (sample / peak) * (height * 0.4);
        if (index === 0) waveCtx.moveTo(x, y); else waveCtx.lineTo(x, y);
    });
    waveCtx.stroke();
}

function drawSpectrum(spectrum) {
    if (!spectrum || !spectrum.frequencies_hz || spectrum.frequencies_hz.length === 0) {
        return drawEmpty(psdCtx, psdCanvas, "PSD unavailable");
    }
    const frequencies = spectrum.frequencies_hz;
    const power = spectrum.power;
    const width = psdCanvas.width;
    const height = psdCanvas.height;
    const peak = Math.max(1e-12, ...power);
    psdCtx.clearRect(0, 0, width, height);
    psdCtx.beginPath();
    psdCtx.strokeStyle = "#8B5CF6";
    psdCtx.lineWidth = 2;
    frequencies.forEach((frequency, index) => {
        const x = Math.min(frequency, 40) / 40 * width;
        const y = height - (power[index] / peak) * (height * 0.9) - 4;
        if (index === 0) psdCtx.moveTo(x, y); else psdCtx.lineTo(x, y);
    });
    psdCtx.stroke();
}

function updateMetrics(metrics) {
    const available = metrics && typeof metrics === "object";
    const percent = (name) => available ? metric(metrics[`${name}_rel`], 1, " %") : "--";
    ["delta", "theta", "alpha", "beta"].forEach((band) => {
        value(`lbl-${band}`, percent(band));
        const fill = document.getElementById(`fill-${band}`);
        if (fill) fill.style.width = available && Number.isFinite(metrics[`${band}_rel`]) ? `${metrics[`${band}_rel`]}%` : "0%";
    });
    
    // Cognitive Load & Classification
    if (runtimeState && runtimeState.cognitive_state) {
        value("m-load", `${runtimeState.cognitive_state} LOAD`);
    } else {
        value("m-load", "--");
    }

    value("m-dom", available ? `${metrics.dominant_band || "--"} (${metric(metrics.dominant_frequency, 2, " Hz")})` : "--");
    value("m-stress", available ? metric(metrics.stress_index, 4) : "--");
    value("m-qual", runtimeState && runtimeState.streaming ? "RUNTIME STREAM" : "NO SIGNAL");
    value("b-tbr", available ? metric(metrics.tbr, 4) : "--");
    value("b-abr", available ? metric(metrics.abr, 4) : "--");
    value("b-eng", available ? metric(metrics.engagement, 4) : "--");
    value("b-total", available ? metric(metrics.total_power, 4) : "--");

    // Real-Time Neurofeedback Protocol Calculations
    if (available && metrics) {
        const stress = metrics.stress_index || 0.5;
        const alphaRel = metrics.alpha_rel || 25;
        const focusScore = Math.max(0, Math.min(100, (1.0 - stress) * 100));
        const statusText = alphaRel >= 30 ? "OPTIMAL TARGET" : (alphaRel >= 20 ? "STABLE REGULATION" : "SUB-THRESHOLD");
        const regulationText = (metrics.tbr || 2.0) <= 2.5 ? "OPTIMAL ATTENTION" : "HIGH THETA WAVES";
        
        value("nf-status", statusText);
        value("nf-focus", metric(focusScore, 1, "%"));
        value("nf-regulation", regulationText);
    } else {
        value("nf-status", "--");
        value("nf-focus", "--");
        value("nf-regulation", "--");
    }
}

function updateSession(state) {
    value("s-id", state.session_id || "--");
    value("s-dur", duration(state.duration_sec));
    value("s-samples", String(state.samples || 0));
    value("s-status", state.state || "IDLE");
    value("mode-badge", `SIMULATOR: ${state.state || "IDLE"}`);
    value("hardware-status", state.hardware && state.hardware.status === "NOT_CONNECTED" ? "Hardware: Not Connected" : "Hardware: Unknown");
}

function updateChannelOptions(channels) {
    const select = document.getElementById("channel-select");
    if (!select || !channels || channels.length === 0) return;
    if (![...select.options].some((option) => option.value === selectedChannel)) selectedChannel = channels[0];
    select.innerHTML = channels.map((channel) => `<option value="${channel}">${channel}</option>`).join("");
    select.value = selectedChannel;
}

async function refreshRuntime() {
    try {
        runtimeState = await api("/api/state");
        latestAnalysis = runtimeState.analysis_available ? await api("/api/analysis") : {analysis: null};
        updateChannelOptions(runtimeState.channels);
        updateSession(runtimeState);
        updateMetrics(runtimeState.metrics);
        drawSpectrum(latestAnalysis.analysis ? latestAnalysis.analysis.spectrum : null);
        const waveform = await api(`/api/waveform?seconds=${selectedWindowSeconds}`);
        drawWaveform(waveform.channels[selectedChannel]);
        value("api-status", "API connected");
    } catch (error) {
        runtimeState = null;
        updateMetrics(null);
        drawEmpty(waveCtx, waveCanvas, "No Data Stream");
        drawEmpty(psdCtx, psdCanvas, "PSD unavailable");
        value("api-status", `API unavailable: ${error.message}`);
    }
}

async function lifecycle(action) {
    try {
        await api(`/api/session/${action}`, {method: "POST"});
    } catch (error) {
        value("api-status", error.message);
    }
    await refreshRuntime();
}

function startSession() { return lifecycle("start"); }
function pauseSession() { return lifecycle("pause"); }
function resumeSession() { return lifecycle("resume"); }
function stopSession() { return lifecycle("stop"); }

async function downloadCurrentReport() {
    return downloadReportForSession(null);
}

async function downloadReportForSession(sessionId) {
    try {
        const url = sessionId ? `/api/report?session_id=${encodeURIComponent(sessionId)}` : "/api/report";
        const response = await api(url, {method: "POST"});
        const blob = await response.blob();
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        const filename = sessionId ? `NeuroSim_${sessionId}.pdf` : "NeuroSim_Runtime_Report.pdf";
        link.download = filename;
        link.click();
        URL.revokeObjectURL(link.href);
    } catch (error) {
        value("api-status", error.message);
    }
}

async function deleteSessionFromHistory(sessionId) {
    if (!sessionId) return;
    try {
        await api(`/api/history/delete?session_id=${encodeURIComponent(sessionId)}`, {method: "POST"});
        await renderHistoryTable();
    } catch (error) {
        value("api-status", error.message);
    }
}

async function inspectSessionDetail(sessionId) {
    const detailDiv = document.getElementById("history-session-detail");
    if (!detailDiv || !sessionId) return;
    try {
        const historyData = await api("/api/history");
        const session = (historyData.sessions || []).find((s) => s.session_id === sessionId);
        if (!session) return;

        detailDiv.innerHTML = `
            <div class="glass-card" style="margin-top:16px; border: 1px solid var(--border-glow);">
                <div class="card-title">Session Detail Inspector: ${session.session_id}</div>
                <div class="grid-4" style="margin-bottom:12px;">
                    <div class="metric-card"><div class="metric-label">MODE</div><div class="metric-val" style="font-size:16px;">${session.mode}</div></div>
                    <div class="metric-card"><div class="metric-label">DURATION</div><div class="metric-val" style="font-size:16px;">${duration(session.duration)}</div></div>
                    <div class="metric-card"><div class="metric-label">DOMINANT BAND</div><div class="metric-val" style="font-size:16px;">${session.dominant_band}</div></div>
                    <div class="metric-card"><div class="metric-label">STRESS INDEX</div><div class="metric-val" style="font-size:16px;">${metric(session.stress_index, 4)}</div></div>
                </div>
                <div style="font-size:13px; color:var(--text-muted);">
                    <strong>Relative Band Powers:</strong> Delta: ${metric(session.rel_delta, 1, "%")} | Theta: ${metric(session.rel_theta, 1, "%")} | Alpha: ${metric(session.rel_alpha, 1, "%")} | Beta: ${metric(session.rel_beta, 1, "%")}
                </div>
            </div>
        `;
    } catch (error) {
        value("api-status", error.message);
    }
}

async function renderHistoryTable() {
    const body = document.getElementById("history-table-body");
    if (!body) return;
    try {
        const historyData = await api("/api/history");
        const sessions = historyData.sessions || [];
        if (sessions.length === 0) {
            if (runtimeState && runtimeState.state === "STOPPED") {
                body.innerHTML = `<tr><td><strong>${runtimeState.session_id}</strong></td><td>Current runtime</td><td>${duration(runtimeState.duration_sec)}</td><td>${runtimeState.state}</td><td>${metric(runtimeState.metrics && runtimeState.metrics.stress_index, 4)}</td><td><button class="btn" style="padding:4px 8px; font-size:12px;" onclick="downloadCurrentReport()">Export PDF</button></td></tr>`;
            } else {
                body.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#94A3B8;">No recorded sessions found in database archive.</td></tr>';
            }
            return;
        }

        body.innerHTML = sessions.map((s) => `
            <tr>
                <td><strong>${s.session_id}</strong></td>
                <td>${s.mode || "SIMULATOR"}</td>
                <td>${duration(s.duration)}</td>
                <td>${s.cognitive_state || "COMPLETED"}</td>
                <td>${metric(s.stress_index, 4)}</td>
                <td>
                    <button class="btn" style="padding:4px 8px; font-size:12px; margin-right:4px;" onclick="inspectSessionDetail('${s.session_id}')">Inspect</button>
                    <button class="btn" style="padding:4px 8px; font-size:12px; margin-right:4px;" onclick="downloadReportForSession('${s.session_id}')">Export PDF</button>
                    <button class="btn btn-rose" style="padding:4px 8px; font-size:12px;" onclick="deleteSessionFromHistory('${s.session_id}')">Delete</button>
                </td>
            </tr>
        `).join("");
    } catch (error) {
        body.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#EF4444;">Failed to load history: ${error.message}</td></tr>`;
    }
}

async function loadResearchSummary() {
    const timelineDiv = document.getElementById("research-longitudinal-timeline");
    try {
        const summary = await api("/api/research/longitudinal");
        value("r-sessions", summary.total_sessions || 0);
        value("r-duration", duration(summary.total_duration_sec));
        value("r-stress", metric(summary.mean_stress_index, 4));

        if (!timelineDiv) return;
        const timeline = summary.timeline || [];
        if (timeline.length === 0) {
            timelineDiv.innerHTML = '<p style="color:#94A3B8; text-align:center; padding:20px;">No research sessions recorded yet in database archive.</p>';
            return;
        }

        timelineDiv.innerHTML = `
            <div style="font-size:14px; font-weight:600; margin-bottom:10px;">Longitudinal Session Progression</div>
            <table>
                <thead>
                    <tr><th>Session ID</th><th>Timestamp</th><th>Duration</th><th>Delta %</th><th>Theta %</th><th>Alpha %</th><th>Beta %</th><th>Stress</th><th>State</th></tr>
                </thead>
                <tbody>
                    ${timeline.map((s) => `
                        <tr>
                            <td><strong>${s.session_id}</strong></td>
                            <td>${s.timestamp}</td>
                            <td>${duration(s.duration)}</td>
                            <td>${metric(s.rel_delta, 1, "%")}</td>
                            <td>${metric(s.rel_theta, 1, "%")}</td>
                            <td>${metric(s.rel_alpha, 1, "%")}</td>
                            <td>${metric(s.rel_beta, 1, "%")}</td>
                            <td>${metric(s.stress_index, 4)}</td>
                            <td><span class="badge">${s.cognitive_state}</span></td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        `;
    } catch (error) {
        value("api-status", error.message);
    }
}

async function exportResearchCSV() {
    try {
        const response = await fetch("/api/research/export_csv");
        const blob = await response.blob();
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "neurosim_research_dataset.csv";
        link.click();
        URL.revokeObjectURL(link.href);
    } catch (error) {
        value("api-status", error.message);
    }
}

async function exportResearchBIDS() {
    try {
        const bidsData = await api("/api/research/bids");
        const blob = new Blob([JSON.stringify(bidsData, null, 2)], {type: "application/json"});
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "bids_dataset_description.json";
        link.click();
        URL.revokeObjectURL(link.href);
    } catch (error) {
        value("api-status", error.message);
    }
}

window.addEventListener("resize", resizeCanvases);
window.addEventListener("DOMContentLoaded", () => {
    resizeCanvases();
    document.getElementById("channel-select").addEventListener("change", (event) => { selectedChannel = event.target.value; refreshRuntime(); });
    document.getElementById("window-select").addEventListener("change", (event) => { selectedWindowSeconds = Number(event.target.value); refreshRuntime(); });
    refreshRuntime();
    window.setInterval(refreshRuntime, 500);
});
