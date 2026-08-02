// PDF Report Export Engine for NeuroSim Web Application

function exportSessionPDF(sessionData) {
    const data = sessionData || {
        id: 'SESS-DEMO',
        duration: '02:30',
        samples: 3750,
        load: 'MODERATE',
        stress: 0.48,
        delta: 25.0,
        theta: 25.0,
        alpha: 35.0,
        beta: 15.0,
        date: new Date().toLocaleString()
    };

    const printWindow = window.open('', '_blank');
    const htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
            <title>NeuroSim Clinical EEG Session Report</title>
            <style>
                body { font-family: 'Helvetica Neue', Arial, sans-serif; padding: 40px; color: #1E293B; line-height: 1.5; }
                .header { border-bottom: 2px solid #06B6D4; padding-bottom: 15px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }
                .title { font-size: 24px; font-weight: 800; color: #0891B2; }
                .subtitle { font-size: 12px; color: #64748B; font-weight: 700; }
                .section { margin-bottom: 25px; }
                .section-title { font-size: 14px; font-weight: 800; color: #334155; text-transform: uppercase; border-bottom: 1px solid #E2E8F0; padding-bottom: 6px; margin-bottom: 12px; }
                .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
                .card { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; }
                .card-label { font-size: 10px; color: #64748B; font-weight: 700; text-transform: uppercase; }
                .card-val { font-size: 20px; font-weight: 800; color: #0891B2; margin-top: 4px; }
                table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                th, td { padding: 10px; border: 1px solid #E2E8F0; text-align: left; font-size: 12px; }
                th { background: #F1F5F9; font-weight: 700; color: #475569; }
                .disclaimer { margin-top: 40px; border-left: 3px solid #EF4444; padding-left: 12px; font-size: 11px; color: #64748B; }
            </style>
        </head>
        <body>
            <div class="header">
                <div>
                    <div class="title">NEUROSIM CLINICAL REPORT</div>
                    <div class="subtitle">SYNTHETIC EEG COGNITIVE ANALYSIS PLATFORM</div>
                </div>
                <div style="text-align: right; font-size: 12px; color: #64748B;">
                    Date: ${data.date}<br>
                    Session: ${data.id}
                </div>
            </div>

            <div class="section">
                <div class="section-title">Session Summary</div>
                <div class="grid">
                    <div class="card"><div class="card-label">Cognitive State</div><div class="card-val">${data.load}</div></div>
                    <div class="card"><div class="card-label">Spectral Stress Index</div><div class="card-val">${data.stress}</div></div>
                    <div class="card"><div class="card-label">Recording Duration</div><div class="card-val">${data.duration}</div></div>
                    <div class="card"><div class="card-label">Samples Analyzed</div><div class="card-val">${data.samples}</div></div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Spectral Band Power Breakdown</div>
                <table>
                    <thead>
                        <tr><th>Band</th><th>Frequency Range</th><th>Relative Power</th><th>Clinical Context</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>Delta (δ)</td><td>0.5 – 4.0 Hz</td><td>${data.delta}%</td><td>Deep sleep, slow-wave activity</td></tr>
                        <tr><td>Theta (θ)</td><td>4.0 – 8.0 Hz</td><td>${data.theta}%</td><td>Drowsiness, meditation, memory</td></tr>
                        <tr><td>Alpha (α)</td><td>8.0 – 13.0 Hz</td><td>${data.alpha}%</td><td>Relaxed alertness, calm focus</td></tr>
                        <tr><td>Beta (β)</td><td>13.0 – 30.0 Hz</td><td>${data.beta}%</td><td>Active concentration, stress</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="disclaimer">
                <strong>BIOMEDICAL DISCLAIMER:</strong> This synthetic EEG cognitive analysis report is generated for research and demonstration purposes. The analytical outputs do not constitute a medical diagnosis.
            </div>

            <script>
                window.onload = function() { window.print(); }
            </script>
        </body>
        </html>
    `;

    printWindow.document.write(htmlContent);
    printWindow.document.close();
}
