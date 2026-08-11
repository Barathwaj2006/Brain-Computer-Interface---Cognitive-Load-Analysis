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
    const hrs = Math.floor(total / 3600);
    const mins = Math.floor((total % 3600) / 60);
    const secs = total % 60;
    if (hrs > 0) {
        return `${String(hrs).padStart(2, "0")}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    }
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function switchTab(tabKey) {
    document.querySelectorAll(".view-screen").forEach((element) => element.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach((element) => element.classList.remove("active"));
    
    const targetScreen = document.getElementById(`screen-${tabKey}`);
    if (targetScreen) targetScreen.classList.add("active");

    const titleMap = {
        dashboard: "EXECUTIVE DASHBOARD",
        monitor: "LIVE MONITORING DASHBOARD",
        band: "QUANTITATIVE BAND ANALYSIS",
        history: "HISTORICAL SESSION ARCHIVE",
        reports: "REPORTS PLATFORM & EXPORT MANAGER",
        research: "RESEARCH PLATFORM & LONGITUDINAL ANALYTICS",
        neurofeedback: "NEUROFEEDBACK TRAINING MODULE",
        hardware: "HARDWARE CONNECTION & STATUS",
        settings: "RUNTIME CONFIGURATION & SETTINGS"
    };
    value("page-header-title", titleMap[tabKey] || "NEUROSIM PLATFORM");

    if (window.event && window.event.currentTarget) window.event.currentTarget.classList.add("active");
    
    if (tabKey === "history") renderHistoryTable();
    if (tabKey === "reports") renderReportsPlatform();
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
    if (waveCanvas) {
        waveCanvas.width = waveCanvas.clientWidth;
        waveCanvas.height = waveCanvas.clientHeight;
    }
    if (psdCanvas) {
        psdCanvas.width = psdCanvas.clientWidth;
        psdCanvas.height = psdCanvas.clientHeight;
    }
}

function drawEmpty(context, canvas, message) {
    if (!context || !canvas) return;
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = "#94A3B8";
    context.font = "14px Segoe UI";
    context.textAlign = "center";
    context.fillText(message, canvas.width / 2, canvas.height / 2);
}

function drawWaveform(samples) {
    if (!samples || samples.length === 0) return drawEmpty(waveCtx, waveCanvas, "No Signal Stream");
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
    const cogText = (runtimeState && runtimeState.cognitive_state) ? `${runtimeState.cognitive_state} LOAD` : "--";
    value("m-load", cogText);
    value("dash-m-load", cogText);

    const domText = available ? `${metrics.dominant_band || "--"} (${metric(metrics.dominant_frequency, 2, " Hz")})` : "--";
    value("m-dom", domText);
    value("dash-m-dom", domText);

    const stressText = available ? metric(metrics.stress_index, 4) : "--";
    value("m-stress", stressText);
    value("dash-m-stress", stressText);

    const qualText = (runtimeState && runtimeState.streaming) ? "RUNTIME STREAM" : "NO SIGNAL";
    value("m-qual", qualText);
    value("dash-m-qual", qualText);

    value("b-tbr", available ? metric(metrics.tbr, 4) : "--");
    value("b-abr", available ? metric(metrics.abr, 4) : "--");
    value("b-eng", available ? metric(metrics.engagement, 4) : "--");
    value("b-total", available ? metric(metrics.total_power, 4) : "--");

    value("b-delta-val", available ? metric(metrics.delta_rel, 1, "%") : "--");
    value("b-theta-val", available ? metric(metrics.theta_rel, 1, "%") : "--");
    value("b-alpha-val", available ? metric(metrics.alpha_rel, 1, "%") : "--");
    value("b-beta-val", available ? metric(metrics.beta_rel, 1, "%") : "--");

    // Real-Time Neurofeedback Protocol Calculations
    if (available && metrics) {
        const protoSelect = document.getElementById("nf-protocol-select");
        const protocol = protoSelect ? protoSelect.value : "alpha";
        const stress = metrics.stress_index || 0.5;
        const alphaRel = metrics.alpha_rel || 25;
        const tbr = metrics.tbr || 1.0;
        
        let focusScore = 0;
        let statusText = "SUB-THRESHOLD";
        let regulationText = "SUB-THRESHOLD";

        if (protocol === "alpha") {
            value("nf-proto-name", "ALPHA ENHANCEMENT");
            focusScore = Math.max(0, Math.min(100, (alphaRel / 35.0) * 100));
            statusText = alphaRel >= 30 ? "OPTIMAL TARGET" : (alphaRel >= 20 ? "STABLE REGULATION" : "SUB-THRESHOLD");
            regulationText = alphaRel >= 25 ? "HIGH ALPHA SYNCHRONY" : "MODERATE SYNC";
        } else if (protocol === "tbr") {
            value("nf-proto-name", "THETA/BETA REDUCTION");
            focusScore = Math.max(0, Math.min(100, Math.max(0, (2.5 - tbr) / 2.5 * 100)));
            statusText = tbr <= 1.5 ? "OPTIMAL TARGET" : (tbr <= 2.5 ? "STABLE REGULATION" : "SUB-THRESHOLD");
            regulationText = tbr <= 2.0 ? "OPTIMAL ATTENTION" : "HIGH THETA WAVES";
        } else {
            value("nf-proto-name", "BETA BOOSTING");
            focusScore = Math.max(0, Math.min(100, stress * 100));
            statusText = stress >= 0.7 ? "OPTIMAL TARGET" : (stress >= 0.4 ? "STABLE REGULATION" : "SUB-THRESHOLD");
            regulationText = stress >= 0.6 ? "ACTIVE ALERTNESS" : "CALM STATE";
        }

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
    const sessId = state.session_id || "--";
    const durText = duration(state.duration_sec);
    const samplesText = String(state.samples || 0);

    value("s-id", sessId);
    value("s-dur", durText);
    value("s-samples", samplesText);
    value("s-status", state.state || "IDLE");

    value("dash-s-id", sessId);
    value("dash-s-dur", durText);
    value("dash-s-samples", samplesText);
    value("dash-s-gaps", String(state.sequence_gaps || 0));

    value("mode-badge", `SIMULATOR: ${state.state || "IDLE"}`);
    
    if (state.streaming) {
        value("hardware-status", "Hardware: Connected (Simulator)");
        value("hw-status-val", "CONNECTED (SIMULATOR)");
        value("hw-source-val", state.source || "SYNTHETIC");
    } else {
        value("hardware-status", "Hardware: Not Connected");
        value("hw-status-val", "Not Connected / Idle");
        value("hw-source-val", "NONE");
    }
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
        drawEmpty(waveCtx, waveCanvas, "No Signal Stream");
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

async function exportSelectedReportPDF() {
    const select = document.getElementById("reports-session-select");
    const sessionId = select ? select.value : null;
    return downloadReportForSession(sessionId);
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
        await renderReportsPlatform();
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
                body.innerHTML = `<tr><td><strong>${runtimeState.session_id}</strong></td><td>Current runtime</td><td>${duration(runtimeState.duration_sec)}</td><td>${runtimeState.state}</td><td>${metric(runtimeState.metrics && runtimeState.metrics.stress_index, 4)}</td><td><button class="btn" style="padding:4px 8px; font-size:12px;" onclick="downloadReportForSession(null)">Export PDF</button></td></tr>`;
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

async function renderReportsPlatform() {
    const select = document.getElementById("reports-session-select");
    if (!select) return;
    try {
        const historyData = await api("/api/history");
        const sessions = historyData.sessions || [];
        
        let optionsHtml = '<option value="">Current Session / Latest</option>';
        optionsHtml += sessions.map(s => `<option value="${s.session_id}">${s.session_id} (${s.mode} - ${duration(s.duration)})</option>`).join("");
        select.innerHTML = optionsHtml;
        
        updateReportPreview();
        select.onchange = updateReportPreview;
    } catch (error) {
        value("api-status", error.message);
    }
}

async function updateReportPreview() {
    const select = document.getElementById("reports-session-select");
    const sessionId = select ? select.value : "";
    try {
        if (!sessionId) {
            value("rep-id", runtimeState ? (runtimeState.session_id || "--") : "--");
            value("rep-dur", runtimeState ? duration(runtimeState.duration_sec) : "--");
            value("rep-src", runtimeState ? (runtimeState.source || "--") : "--");
            value("rep-state", runtimeState ? (runtimeState.cognitive_state || "--") : "--");
            const m = runtimeState ? runtimeState.metrics : null;
            value("rep-stress", m ? metric(m.stress_index, 4) : "--");
            value("rep-band", m ? (m.dominant_band || "--") : "--");
            value("rep-tbr", m ? metric(m.tbr, 4) : "--");
            value("rep-abr", m ? metric(m.abr, 4) : "--");
        } else {
            const historyData = await api("/api/history");
            const session = (historyData.sessions || []).find((s) => s.session_id === sessionId);
            if (session) {
                value("rep-id", session.session_id);
                value("rep-dur", duration(session.duration));
                value("rep-src", session.mode || "SIMULATOR");
                value("rep-state", session.cognitive_state || "COMPLETED");
                value("rep-stress", metric(session.stress_index, 4));
                value("rep-band", session.dominant_band || "--");
                const b = session.rel_beta || 25.0;
                const tbr = session.rel_theta / (b + 1e-6);
                const abr = session.rel_alpha / (b + 1e-6);
                value("rep-tbr", metric(tbr, 4));
                value("rep-abr", metric(abr, 4));
            }
        }
    } catch (error) {
        value("api-status", error.message);
    }
}

async function loadResearchSummary() {
    const timelineDiv = document.getElementById("research-longitudinal-timeline");
    const cmpA = document.getElementById("cmp-sess-a");
    const cmpB = document.getElementById("cmp-sess-b");
    try {
        const summary = await api("/api/research/longitudinal");
        value("r-sessions", summary.total_sessions || 0);
        value("r-duration", duration(summary.total_duration_sec));
        value("r-stress", metric(summary.mean_stress_index, 4));

        const timeline = summary.timeline || [];
        if (cmpA && cmpB) {
            const opts = '<option value="">Select Session</option>' + timeline.map(s => `<option value="${s.session_id}">${s.session_id} (${s.cognitive_state})</option>`).join("");
            cmpA.innerHTML = opts;
            cmpB.innerHTML = opts;
        }

        if (!timelineDiv) return;
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

async function runSessionComparison() {
    const cmpA = document.getElementById("cmp-sess-a");
    const cmpB = document.getElementById("cmp-sess-b");
    const resDiv = document.getElementById("comparison-results-div");
    if (!cmpA || !cmpB || !resDiv) return;
    const idA = cmpA.value;
    const idB = cmpB.value;
    if (!idA || !idB) {
        resDiv.innerHTML = '<p style="color:#F59E0B;">Please select two sessions to compare.</p>';
        return;
    }
    try {
        const compData = await api(`/api/research/compare?ids=${encodeURIComponent(idA)},${encodeURIComponent(idB)}`);
        const sessions = compData.sessions || [];
        if (sessions.length < 2) {
            resDiv.innerHTML = '<p style="color:#EF4444;">Failed to retrieve both session records for comparison.</p>';
            return;
        }
        const sA = sessions[0];
        const sB = sessions[1];

        resDiv.innerHTML = `
            <table>
                <thead>
                    <tr><th>Metric</th><th>Session A (${sA.session_id})</th><th>Session B (${sB.session_id})</th><th>Difference</th></tr>
                </thead>
                <tbody>
                    <tr><td>Duration</td><td>${duration(sA.duration)}</td><td>${duration(sB.duration)}</td><td>${duration(Math.abs(sB.duration - sA.duration))}</td></tr>
                    <tr><td>Cognitive State</td><td>${sA.cognitive_state}</td><td>${sB.cognitive_state}</td><td>--</td></tr>
                    <tr><td>Stress Index</td><td>${metric(sA.stress_index, 4)}</td><td>${metric(sB.stress_index, 4)}</td><td>${metric(sB.stress_index - sA.stress_index, 4)}</td></tr>
                    <tr><td>Dominant Band</td><td>${sA.dominant_band}</td><td>${sB.dominant_band}</td><td>--</td></tr>
                    <tr><td>Delta %</td><td>${metric(sA.rel_delta, 1, "%")}</td><td>${metric(sB.rel_delta, 1, "%")}</td><td>${metric(sB.rel_delta - sA.rel_delta, 1, "%")}</td></tr>
                    <tr><td>Theta %</td><td>${metric(sA.rel_theta, 1, "%")}</td><td>${metric(sB.rel_theta, 1, "%")}</td><td>${metric(sB.rel_theta - sA.rel_theta, 1, "%")}</td></tr>
                    <tr><td>Alpha %</td><td>${metric(sA.rel_alpha, 1, "%")}</td><td>${metric(sB.rel_alpha, 1, "%")}</td><td>${metric(sB.rel_alpha - sA.rel_alpha, 1, "%")}</td></tr>
                    <tr><td>Beta %</td><td>${metric(sA.rel_beta, 1, "%")}</td><td>${metric(sB.rel_beta, 1, "%")}</td><td>${metric(sB.rel_beta - sA.rel_beta, 1, "%")}</td></tr>
                </tbody>
            </table>
        `;
    } catch (error) {
        resDiv.innerHTML = `<p style="color:#EF4444;">Comparison failed: ${error.message}</p>`;
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
    const chSel = document.getElementById("channel-select");
    if (chSel) chSel.addEventListener("change", (event) => { selectedChannel = event.target.value; refreshRuntime(); });
    const winSel = document.getElementById("window-select");
    if (winSel) winSel.addEventListener("change", (event) => { selectedWindowSeconds = Number(event.target.value); refreshRuntime(); });
    const nfSel = document.getElementById("nf-protocol-select");
    if (nfSel) nfSel.addEventListener("change", refreshRuntime);
    refreshRuntime();
    window.setInterval(refreshRuntime, 500);
});
