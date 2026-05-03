const API_BASE = ''; // Relative for deployment
let charts = {};
let currentHistory = [];
let hasAnalyzed = false;

const powerMap = {
    'Air Conditioning': 1500, 'Computer': 200, 'Dishwasher': 1200, 'Fridge': 200,
    'Heater': 2000, 'Lights': 60, 'Microwave': 800, 'Oven': 2000, 'TV': 100,
    'Washing Machine': 500, 'Other': 300
};

// ================= UI NAVIGATION =================
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

function showPage(pageId, el) {
    // Close sidebar on mobile after clicking
    if (window.innerWidth <= 768) {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.classList.remove('open');
    }

    document.querySelectorAll('.page').forEach(page => {
        page.style.display = 'none';
        page.classList.remove('active');
    });
    const targetPage = document.getElementById(pageId + '-page');
    if (targetPage) targetPage.style.display = 'block';

    document.querySelectorAll('.menu-item').forEach(item => item.classList.remove('active'));
    if (el) el.classList.add('active');

    if (pageId === 'analytics' || pageId === 'reports') {
        if (hasAnalyzed) {
            loadAllData();
        } else if (pageId === 'reports') {
            // Reports can show historical data, but charts should stay empty as per requirement
            loadAllData(); 
        }
    }
}

function switchMode(mode, el) {
    document.getElementById('manual-input-zone').style.display = 'none';
    document.getElementById('csv-input-zone').style.display = 'none';
    if (mode === 'manual') document.getElementById('manual-input-zone').style.display = 'block';
    if (mode === 'csv') document.getElementById('csv-input-zone').style.display = 'block';

    document.querySelectorAll('.tab-selector .tab-btn').forEach(btn => btn.classList.remove('active'));
    if (el) el.classList.add('active');
}

// ================= WIDGET CONTROLS =================
function updateTempLabel(val) {
    document.getElementById('temp-val').innerText = val;
}

function incrementHSize() {
    let input = document.getElementById('hsize');
    let display = document.getElementById('hsize-val');
    let val = parseInt(input.value) + 1;
    if (val <= 10) { input.value = val; display.innerText = val; }
}

function decrementHSize() {
    let input = document.getElementById('hsize');
    let display = document.getElementById('hsize-val');
    let val = parseInt(input.value) - 1;
    if (val >= 1) { input.value = val; display.innerText = val; }
}

function toggleAC() {
    const toggle = document.getElementById('ac-toggle');
    const input = document.getElementById('acusage');
    const label = document.getElementById('ac-label');
    toggle.classList.toggle('active');
    const isOn = toggle.classList.contains('active');
    input.value = isOn ? '1' : '0';
    if (label) label.innerText = isOn ? 'ON' : 'OFF';
}

function autoFillPower(selectEl) {
    const row = selectEl.closest('.appliance-row');
    const powerInput = row.querySelector('.appliance-power');
    const appliance = selectEl.value;
    powerInput.value = powerMap[appliance] || 300;
}

// ================= CUSTOM DROPDOWN LOGIC =================
function toggleCustomSelect(el, event) {
    event.stopPropagation();
    
    // Lift the parent card to ensure dropdown appears above other cards
    const parentCard = el.closest('.glass-card');
    
    // Close other dropdowns and reset their card z-index
    document.querySelectorAll('.custom-select').forEach(s => {
        if (s !== el) {
            s.classList.remove('active');
            const card = s.closest('.glass-card');
            if (card) card.style.zIndex = "";
        }
    });

    const isOpening = !el.classList.contains('active');
    el.classList.toggle('active');

    if (parentCard) {
        parentCard.style.zIndex = isOpening ? "100" : "";
    }
}

function handleOptionClick(optionEl, event) {
    event.stopPropagation();
    const dropdown = optionEl.closest('.custom-select');
    const triggerText = dropdown.querySelector('.select-trigger span');
    const nativeSelect = dropdown.querySelector('select');
    const val = optionEl.getAttribute('data-value');
    const text = optionEl.innerText;

    // Update UI
    if (triggerText) triggerText.innerText = text;
    dropdown.querySelectorAll('.option').forEach(opt => opt.classList.remove('selected'));
    optionEl.classList.add('selected');
    dropdown.classList.remove('active');

    // Sync with native select
    if (nativeSelect) {
        nativeSelect.value = val;
        // Specifically for appliance rows to trigger power update
        if (nativeSelect.classList.contains('appliance-type')) {
            autoFillPower(nativeSelect);
        }
    }
}

// Close dropdowns on click outside
window.addEventListener('click', () => {
    document.querySelectorAll('.custom-select').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.glass-card').forEach(c => c.style.zIndex = "");
});

function removeApplianceRow(btn) {
    const row = btn.closest('.appliance-row');
    if (document.querySelectorAll('.appliance-row').length > 1) {
        row.remove();
    }
}

function addApplianceRow() {
    const list = document.getElementById('appliance-list');
    const firstRow = list.querySelector('.appliance-row');
    const newRow = firstRow.cloneNode(true);
    
    // Reset values in cloned row
    newRow.querySelector('.appliance-time').value = "5";
    newRow.querySelector('.remove-btn').style.visibility = 'visible';
    
    // Reset custom dropdown in cloned row
    const customSelect = newRow.querySelector('.custom-select');
    if (customSelect) {
        customSelect.classList.remove('active');
        customSelect.querySelector('.select-trigger span').innerText = "Air Conditioning";
        customSelect.querySelector('select.appliance-type').value = "Air Conditioning";
        customSelect.querySelectorAll('.option').forEach(opt => opt.classList.remove('selected'));
        customSelect.querySelector('.option[data-value="Air Conditioning"]').classList.add('selected');
    }
    
    list.appendChild(newRow);
    
    // Make sure the first row's remove button is also visible if there are multiple rows
    list.querySelector('.remove-btn').style.visibility = 'visible';
}

// ================= PREDICTIONS & API =================
async function predictManual() {
    const rows = document.querySelectorAll('.appliance-row');
    const appliancesBatch = [];
    
    document.getElementById('loading-overlay').style.display = 'flex';
    document.getElementById('result-placeholder').style.display = 'none';
    document.getElementById('prediction-result').style.display = 'block';
    document.getElementById('energy-val').innerText = "Analyzing...";

    const costPerUnit = parseFloat(document.getElementById('cost-per-unit').value) || 8;

    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        appliancesBatch.push({
            Temperature: parseFloat(document.getElementById('temp').value),
            TimeOfDay: document.getElementById('time-of-day').value,
            DayType: document.getElementById('day-type').value,
            Season: document.getElementById('season').value,
            Appliance: row.querySelector('.appliance-type').value,
            Power: parseFloat(row.querySelector('.appliance-power').value),
            UsageTime: parseFloat(row.querySelector('.appliance-time').value),
            ACUsage: parseInt(document.getElementById('acusage').value),
            HouseholdSize: parseInt(document.getElementById('hsize').value),
            CostPerUnit: costPerUnit
        });
    }

    try {
        const response = await fetch(`${API_BASE}/predict_batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(appliancesBatch)
        });
        const result = await response.json();
        if (response.ok) {
            let totalPrediction = 0;
            let totalCost = 0;
            let suggestionsArray = [];
            
            result.results.forEach(res => {
                totalPrediction += res.prediction;
                totalCost += res.estimated_cost;
                if (res.suggestions) suggestionsArray = suggestionsArray.concat(res.suggestions);
            });

            displayResult({
                prediction: totalPrediction,
                estimated_cost: totalCost,
                suggestions: suggestionsArray.slice(0, 3)
            });

            // UPDATE CHARTS ONLY WITH LATEST PREDICTION (REQUIREMENT 2)
            hasAnalyzed = true;
            renderCharts(result.results);
            
            // REFRESH REPORTS/HISTORY SEPARATELY
            await loadAllData();
        } else {
            alert("Error: " + result.error);
        }
    } catch (e) {
        console.error("Manual Prediction Error:", e);
        alert("Failed to connect to AI server. Please check if the backend is running.");
    } finally {
        document.getElementById('loading-overlay').style.display = 'none';
    }
}

function displayResult(result) {
    document.getElementById('result-placeholder').style.display = 'none';
    document.getElementById('prediction-result').style.display = 'block';
    
    document.getElementById('energy-val').innerText = result.prediction.toFixed(2);
    document.getElementById('cost-val').innerText = result.estimated_cost.toFixed(2);
    
    const goal = parseFloat(document.getElementById('energy-goal').value);
    const goalEl = document.getElementById('goal-comparison');
    
    if (result.prediction <= goal) {
        goalEl.innerHTML = `✅ Under budget by ${(goal - result.prediction).toFixed(1)} kWh`;
        goalEl.style.color = 'var(--success)';
        goalEl.style.backgroundColor = 'var(--success-soft, rgba(34, 197, 94, 0.1))';
    } else {
        goalEl.innerHTML = `⚠️ Over budget by ${(result.prediction - goal).toFixed(1)} kWh`;
        goalEl.style.color = 'var(--danger)';
        goalEl.style.backgroundColor = 'var(--danger-soft, rgba(239, 68, 68, 0.1))';
    }

    // Display suggestions
    const suggestionsBox = document.getElementById('suggestions');
    if (result.suggestions && result.suggestions.length > 0) {
        suggestionsBox.innerHTML = result.suggestions.map(s => `
            <div style="padding: 14px 18px; border-left: 4px solid var(--accent); background: var(--surface-alt); margin-bottom: 12px; border-radius: var(--radius-sm); font-size: 13px; box-shadow: var(--shadow-sm); display: flex; gap: 12px; align-items: flex-start;">
                <div style="font-size: 20px;">${s.icon || '💡'}</div>
                <div>
                    <strong style="color: var(--text-primary); font-size: 14px; display: block; margin-bottom: 4px;">${s.title || 'Tip'}</strong>
                    <span style="color: var(--text-secondary); line-height: 1.5;">${s.desc || s}</span>
                </div>
            </div>
        `).join('');
    } else {
        suggestionsBox.innerHTML = `<div style="padding: 15px; text-align: center; color: var(--text-muted);">Usage looks optimal!</div>`;
    }
}

async function predictCSV() {
    const fileInput = document.getElementById('csv-file');
    if (fileInput.files.length === 0) {
        alert("Please select a CSV file first.");
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    document.getElementById('loading-overlay').style.display = 'flex';
    document.getElementById('file-name').innerText = "Uploading CSV...";

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        if (response.ok) {
            document.getElementById('file-name').innerText = `Success: ${result.message}`;
            
            // Calculate totals for CSV results to show in dashboard
            let totalPrediction = 0;
            let totalCost = 0;
            result.results.forEach(res => {
                totalPrediction += res.prediction;
                totalCost += res.estimated_cost;
            });

            displayResult({
                prediction: totalPrediction,
                estimated_cost: totalCost,
                suggestions: [] // CSV usually doesn't return specific suggestions for every row
            });

            // UPDATE CHARTS ONLY WITH LATEST PREDICTION (REQUIREMENT 2)
            hasAnalyzed = true;
            renderCharts(result.results);
            
            // REFRESH REPORTS/HISTORY SEPARATELY
            await loadAllData();
            
            // STRICT REQUIREMENT: No setTimeout for mode switching
            switchMode('manual');
        } else {
            document.getElementById('file-name').innerText = `Error: ${result.error}`;
        }
    } catch (e) {
        console.error("CSV Error:", e);
        document.getElementById('file-name').innerText = `Network Error`;
    } finally {
        document.getElementById('loading-overlay').style.display = 'none';
    }
}

// Automatically update filename text on file selection
document.getElementById('csv-file')?.addEventListener('change', function() {
    if (this.files.length > 0) {
        document.getElementById('file-name').innerText = this.files[0].name;
        document.getElementById('upload-btn').style.display = 'inline-block';
    }
});

// ================= HISTORY & CHARTS =================
async function loadAllData() {
    try {
        const response = await fetch(`${API_BASE}/reports`);
        if (!response.ok) throw new Error("Server response not OK");
        const data = await response.json();
        currentHistory = data || [];
        
        // Populate reports/history only (REQUIREMENT 3)
        renderModalData();
        applyFilters();
    } catch (e) {
        console.error("Failed to fetch all data:", e);
    }
}

function destroyCharts() {
    Object.keys(charts).forEach(key => {
        if (charts[key] && typeof charts[key].destroy === 'function') {
            charts[key].destroy();
        }
    });
    charts = {};
}

function renderCharts(sessionData) {
    if (!hasAnalyzed) return;
    if (!sessionData || sessionData.length === 0) return;

    // Destroy previous instances to ensure "Reset previous data" (REQUIREMENT 1 & 5)
    destroyCharts();

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const accentColor = isDark ? '#ff9500' : '#eb6200';
    const textColor = isDark ? '#f8fafc' : '#0f172a';
    const mutedColor = isDark ? '#64748b' : '#94a3b8';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';

    const noDataConfig = {
        text: 'No data yet.', align: 'center', verticalAlign: 'middle',
        style: { color: mutedColor, fontSize: '15px' }
    };

    // TIME AXIS FIX (REQUIREMENT 3)
    // Use actual timestamp if available (CSV), otherwise index-based
    const trendData = sessionData.map((item, index) => ({
        x: item.timestamp && item.timestamp.trim() !== "" ? item.timestamp : `Pt ${index + 1}`,
        y: item.prediction || item.predicted_energy || 0
    }));

    const trendOptions = {
        series: [{ name: 'Energy (kWh)', data: trendData }],
        chart: { type: 'area', height: 280, toolbar: { show: false }, fontFamily: 'Inter, sans-serif' },
        colors: [accentColor],
        stroke: { curve: 'straight', width: 3 },
        markers: { size: 6, colors: ['#fff'], strokeColors: accentColor, strokeWidth: 3, hover: { size: 8 } },
        fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.05, stops: [0, 90, 100] } },
        noData: noDataConfig,
        dataLabels: { enabled: false },
        xaxis: { 
            type: 'category', 
            labels: { show: true, rotate: -45, style: { colors: mutedColor, fontSize: '10px' } },
            title: { text: 'Input Sequence', style: { fontWeight: 700, color: textColor } }
        },
        yaxis: { 
            labels: { formatter: (val) => val.toFixed(2), style: { colors: mutedColor } },
            title: { text: 'Energy (kWh)', style: { fontWeight: 700, color: textColor } }
        },
        title: { text: 'Prediction Sequence Analysis', align: 'left', style: { fontSize: '14px', fontWeight: 'bold', color: textColor } },
        grid: { borderColor: gridColor, strokeDashArray: 4 },
        tooltip: { theme: isDark ? 'dark' : 'light' }
    };

    // Render Dashboard Trend
    if(document.querySelector("#trend-chart")) {
        charts.trend = new ApexCharts(document.querySelector("#trend-chart"), trendOptions);
        charts.trend.render();
    }
    
    // Render Analytics Trend
    if(document.querySelector("#analytics-trend-chart")) {
        charts.analyticsTrend = new ApexCharts(document.querySelector("#analytics-trend-chart"), {...trendOptions, chart: {...trendOptions.chart, height: 350}});
        charts.analyticsTrend.render();
    }

    // Distribution Data (Donut)
    // For large datasets, we still need to aggregate everything to be accurate
    let applianceTotals = {};
    sessionData.forEach(item => {
        let app = item.appliance || 'Other';
        applianceTotals[app] = (applianceTotals[app] || 0) + (item.prediction || item.predicted_energy || 0);
    });

    const distOptions = {
        series: Object.values(applianceTotals),
        labels: Object.keys(applianceTotals),
        chart: { type: 'donut', height: 320, fontFamily: 'Inter, sans-serif' },
        colors: ['#ff9500', '#3b82f6', '#34c759', '#af52de', '#ff3b30', '#facc15', '#0ea5e9'],
        stroke: { width: 3, colors: ['#fff'] },
        plotOptions: { pie: { donut: { size: '65%' } } },
        dataLabels: { 
            enabled: true, 
            formatter: (val) => val.toFixed(1) + "%",
            style: { fontSize: '12px', fontWeight: 'bold' }
        },
        title: { text: 'Energy Split by Appliance', align: 'left', style: { fontSize: '14px', fontWeight: 'bold', color: textColor } },
        legend: { position: 'bottom', labels: { colors: textColor } },
        tooltip: { theme: isDark ? 'dark' : 'light' }
    };

    if(document.querySelector("#distribution-chart")) {
        charts.distribution = new ApexCharts(document.querySelector("#distribution-chart"), distOptions);
        charts.distribution.render();
    }

    // Comparison Data (Bar Chart)
    const comparisonData = sessionData.map((item, index) => ({
        x: item.appliance || `Pt ${index + 1}`,
        y: item.prediction || item.predicted_energy || 0
    }));

    const comparisonOptions = {
        series: [{ name: 'Energy (kWh)', data: comparisonData }],
        chart: { type: 'bar', height: 320, toolbar: { show: false }, fontFamily: 'Inter, sans-serif' },
        colors: [accentColor],
        plotOptions: { bar: { borderRadius: 8, columnWidth: '50%', dataLabels: { position: 'top' } } },
        dataLabels: { 
            enabled: true, 
            formatter: (val) => val.toFixed(2),
            offsetY: -20,
            style: { fontSize: '10px', colors: ["#334155"] }
        },
        xaxis: { type: 'category', labels: { style: { colors: mutedColor } } },
        yaxis: { labels: { style: { colors: mutedColor } } },
        title: { text: 'Individual Prediction Comparison', align: 'left', style: { color: textColor } },
        grid: { borderColor: gridColor, strokeDashArray: 4 },
        tooltip: { theme: isDark ? 'dark' : 'light' }
    };

    if(document.querySelector("#comparison-chart")) {
        charts.comparison = new ApexCharts(document.querySelector("#comparison-chart"), comparisonOptions);
        charts.comparison.render();
    }
}

// ================= MODAL & REPORTS =================
function openStoredDataModal() {
    document.getElementById('stored-data-modal').style.display = 'flex';
    renderModalData();
}

function closeStoredDataModal() {
    document.getElementById('stored-data-modal').style.display = 'none';
}

function renderModalData() {
    const tbody = document.querySelector('#modal-history-table tbody');
    if (!tbody) return;
    
    let data = [...currentHistory];
    
    // Sort logic
    const sortVal = document.getElementById('modal-sort')?.value || 'date-desc';
    if (sortVal === 'date-desc') { /* Already DESC from backend */ }
    else if (sortVal === 'date-asc') data.reverse();
    else if (sortVal === 'energy-desc') data.sort((a, b) => (b.predicted_energy || b.prediction || 0) - (a.predicted_energy || a.prediction || 0));

    // Grouping logic
    const isGrouped = document.getElementById('modal-group')?.checked;
    if (isGrouped) {
        const grouped = {};
        data.forEach(item => {
            const app = item.appliance || 'Unknown';
            if (!grouped[app]) {
                grouped[app] = { ...item, count: 1 };
            } else {
                // Sum up for averaging later
                grouped[app].predicted_energy = (grouped[app].predicted_energy || grouped[app].prediction || 0) + (item.predicted_energy || item.prediction || 0);
                grouped[app].count++;
            }
        });
        // Convert back to array and average predictions
        data = Object.values(grouped).map(item => ({
            ...item,
            predicted_energy: item.predicted_energy / item.count,
            timestamp: `Avg of ${item.count} entries`
        }));
    }
    
    tbody.innerHTML = '';
    // Performance: Slice data to prevent OOM/Freeze and use join
    const displayData = data.slice(0, 500); 
    const html = displayData.map(item => `
        <tr>
            <td>${item.timestamp}</td>
            <td>Manual</td>
            <td><strong>${item.appliance || 'Unknown'}</strong></td>
            <td>${item.temperature || 25}°C</td>
            <td>${item.household_size || 3}</td>
            <td>${item.usage_time || 5}h</td>
            <td>${item.ac_usage ? 'Yes' : 'No'}</td>
            <td style="font-weight: 700; color: var(--accent);">${(item.predicted_energy || item.prediction || 0).toFixed(2)}</td>
        </tr>
    `).join('');
    
    tbody.innerHTML = html;
    if (data.length > 500) {
        tbody.innerHTML += `<tr><td colspan="8" style="text-align:center; color:var(--text-muted); padding:10px;">Showing latest 500 of ${data.length} records. Download CSV for full report.</td></tr>`;
    }
}

function downloadCSV() {
    if(!currentHistory.length) return alert("No data to download");
    let csv = "Timestamp,Appliance,Temperature,UsageTime,Prediction\n";
    currentHistory.forEach(r => {
        csv += `${r.timestamp},${r.appliance},${r.temperature},${r.usage_time},${(r.predicted_energy || r.prediction || 0).toFixed(2)}\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = "Energy_Report.csv";
    a.click();
}

function downloadModalCSV() {
    downloadCSV();
}

async function clearStoredData() {
    if(confirm("Are you sure you want to delete all history?")) {
        try {
            await fetch(`${API_BASE}/reset`, { method: 'POST' });
            hasAnalyzed = false; // Reset analysis state on clear
            await loadAllData();
            closeStoredDataModal();
        } catch (e) {}
    }
}

// ================= REPORTS FILTERS =================
function applyFilters() {
    const search = (document.getElementById('filter-search')?.value || '').toLowerCase();
    const dateVal = document.getElementById('filter-date')?.value || '';
    const typeVal = document.getElementById('filter-type')?.value || 'All';
    const sortVal = document.getElementById('sort-energy')?.value || 'none';

    let data = [...currentHistory];

    if (search) data = data.filter(r => (r.appliance || '').toLowerCase().includes(search));
    if (dateVal) data = data.filter(r => r.timestamp && r.timestamp.startsWith(dateVal));
    if (typeVal !== 'All') data = data.filter(r => r.appliance === typeVal);

    if (sortVal === 'desc') data.sort((a, b) => (b.predicted_energy || b.prediction || 0) - (a.predicted_energy || a.prediction || 0));
    else if (sortVal === 'asc') data.sort((a, b) => (a.predicted_energy || a.prediction || 0) - (b.predicted_energy || b.prediction || 0));
    else { /* Default: already newest first from backend */ }

    const tbody = document.querySelector('#full-history-table tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    const displayData = data.slice(0, 500);
    const html = displayData.map(item => `
        <tr>
            <td>${item.timestamp || '—'}</td>
            <td><strong>${item.appliance || '—'}</strong></td>
            <td>${item.temperature || '—'}°C</td>
            <td>${item.household_size || 3}</td>
            <td>${item.usage_time || '—'}h</td>
            <td>${item.ac_usage ? 'Yes' : 'No'}</td>
            <td style="font-weight:700; color:var(--accent);">${(item.predicted_energy || item.prediction || 0).toFixed(2)}</td>
        </tr>
    `).join('');
    
    tbody.innerHTML = html;
    if (data.length > 500) {
        tbody.innerHTML += `<tr><td colspan="7" style="text-align:center; color:var(--text-muted); padding:10px;">Showing latest 500 of ${data.length} matches.</td></tr>`;
    }
}

// ================= THEME MANAGEMENT =================
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    // Update theme toggle UI
    document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.style.borderColor = 'var(--border)';
        btn.style.background = 'var(--surface-alt)';
        btn.style.color = 'var(--text-secondary)';
    });
    const activeBtn = document.getElementById(`theme-${theme}`);
    if (activeBtn) {
        activeBtn.style.borderColor = 'var(--accent)';
        activeBtn.style.background = 'var(--accent-soft)';
        activeBtn.style.color = 'var(--accent)';
    }

    // Refresh charts if we have data to apply new theme colors
    if (currentHistory && currentHistory.length > 0) {
        renderCharts(currentHistory);
    }
}

async function trainModel() {
    try {
        const btn = event.currentTarget;
        const originalText = btn.innerText;
        btn.innerText = 'Training...';
        btn.disabled = true;

        const res = await fetch(`${API_BASE}/train`, { method: 'POST' });
        const data = await res.json();
        
        // STRICT REQUIREMENT: No setInterval polling
        alert("Model training started in background.");
        btn.innerText = "Training Started";

    } catch(e) {
        alert('Failed to retrain model. Check server connection.');
    }
}

// ================= INIT =================
document.addEventListener('DOMContentLoaded', () => {
    // Apply saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);

    // Check AI status
    fetch(`${API_BASE}/status`)
        .then(res => res.json())
        .then(data => {
            const statusEl = document.getElementById('ai-status-text');
            if (statusEl) statusEl.innerText = data.status === 'Training' ? '🟡 Training' : '🟢 Ready';
            
            const accuracyEl = document.getElementById('model-accuracy');
            if (accuracyEl) accuracyEl.innerText = data.accuracy || '—';
        }).catch(() => {});

    // Initial data load - REMOVED for clean start
    // loadAllData();
});

