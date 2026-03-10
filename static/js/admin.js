let allGuests = [];

// Theme toggle
function initTheme() {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;
    toggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme') || 'dark';
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    loadStats();
    loadGuests();
    checkPrinter();
    setupEventListeners();

    // Auto-refresh stats every 10s
    setInterval(loadStats, 10000);
    setInterval(loadGuests, 15000);
});

function setupEventListeners() {
    // CSV upload
    document.getElementById('csv-input').addEventListener('change', handleCSVUpload);

    // Drag and drop
    const dropArea = document.getElementById('upload-area');
    dropArea.addEventListener('dragover', e => {
        e.preventDefault();
        dropArea.classList.add('dragover');
    });
    dropArea.addEventListener('dragleave', () => dropArea.classList.remove('dragover'));
    dropArea.addEventListener('drop', e => {
        e.preventDefault();
        dropArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.name.endsWith('.csv')) uploadCSV(file);
        else toast('Please drop a .csv file', 'error');
    });

    // Luma sync
    document.getElementById('btn-sync-luma').addEventListener('click', syncLuma);

    // QR code
    document.getElementById('btn-qr').addEventListener('click', generateQR);

    // Clear data
    document.getElementById('btn-clear-data').addEventListener('click', clearAllData);

    // Table search
    document.getElementById('table-search').addEventListener('input', e => {
        renderGuestTable(e.target.value);
    });
}

async function loadStats() {
    try {
        const resp = await fetch('/api/stats');
        const data = await resp.json();
        document.getElementById('stat-total').textContent = data.total_guests;
        document.getElementById('stat-checkedin').textContent = data.checked_in;
        document.getElementById('stat-remaining').textContent = data.remaining;
        if (data.event_name) {
            document.getElementById('admin-event-name').textContent = data.event_name;
            document.title = 'Innovate Together - Admin';
        }
    } catch (e) {
        console.warn('Stats load failed:', e);
    }
}

async function loadGuests() {
    try {
        const resp = await fetch('/admin/api/guests');
        allGuests = await resp.json();
        document.getElementById('table-count').textContent = allGuests.length;
        renderGuestTable(document.getElementById('table-search').value);
    } catch (e) {
        console.warn('Guest load failed:', e);
    }
}

function renderGuestTable(filter = '') {
    const tbody = document.getElementById('guest-tbody');
    const lowerFilter = filter.toLowerCase();

    const filtered = filter
        ? allGuests.filter(g =>
            g.name.toLowerCase().includes(lowerFilter) ||
            (g.company || '').toLowerCase().includes(lowerFilter) ||
            (g.email || '').toLowerCase().includes(lowerFilter)
        )
        : allGuests;

    tbody.innerHTML = filtered.map(g => {
        const isCheckedIn = !!g.checked_in_at;
        const statusBadge = isCheckedIn
            ? `<span class="status-badge checked">Checked In</span>`
            : `<span class="status-badge pending">Not Yet</span>`;

        const checkinTime = isCheckedIn
            ? new Date(g.checked_in_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : '';

        const actions = isCheckedIn
            ? `<button class="action-btn" onclick="undoCheckin('${g.api_id}')">Undo</button>
               <button class="action-btn" onclick="reprintBadge('${g.api_id}')">Reprint</button>`
            : `<button class="action-btn" onclick="forceCheckin('${g.api_id}')">Check In</button>`;

        return `<tr>
            <td><strong>${escapeHtml(g.name)}</strong><br><small>${escapeHtml(g.email || '')}</small></td>
            <td>${escapeHtml(g.company || '')}</td>
            <td>${escapeHtml(g.job_title || '')}</td>
            <td>${statusBadge} ${checkinTime}</td>
            <td>${actions}</td>
        </tr>`;
    }).join('');
}

async function handleCSVUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    await uploadCSV(file);
    e.target.value = '';
}

async function uploadCSV(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const resp = await fetch('/admin/api/upload-csv', { method: 'POST', body: formData });
        const data = await resp.json();
        if (resp.ok) {
            toast(`Imported ${data.imported} guests`, 'success');
            loadStats();
            loadGuests();
        } else {
            toast('Import failed: ' + (data.detail || 'Unknown error'), 'error');
        }
    } catch (e) {
        toast('Upload error: ' + e.message, 'error');
    }
}

async function syncLuma() {
    toast('Syncing from Luma API...');
    try {
        const resp = await fetch('/admin/api/sync-luma', { method: 'POST' });
        const data = await resp.json();
        if (resp.ok) {
            toast(`Synced ${data.synced} guests from Luma`, 'success');
            loadStats();
            loadGuests();
        } else {
            toast('Sync failed: ' + (data.detail || 'Unknown error'), 'error');
        }
    } catch (e) {
        toast('Sync error: ' + e.message, 'error');
    }
}

async function clearAllData() {
    const count = allGuests.length;
    if (!confirm(`This will permanently delete all ${count} guests and check-in data.\n\nAre you sure?`)) {
        return;
    }
    if (!confirm('This cannot be undone. Clear all data?')) {
        return;
    }
    try {
        const resp = await fetch('/admin/api/clear-data', { method: 'POST' });
        if (resp.ok) {
            toast('All data cleared', 'success');
            loadStats();
            loadGuests();
        } else {
            toast('Failed to clear data', 'error');
        }
    } catch (e) {
        toast('Error: ' + e.message, 'error');
    }
}

async function forceCheckin(apiId) {
    try {
        const resp = await fetch(`/admin/api/force-checkin/${apiId}`, { method: 'POST' });
        const data = await resp.json();
        if (data.status === 'success') {
            toast(`Checked in ${data.name}`, 'success');
            loadStats();
            loadGuests();
        } else {
            toast('Check-in failed: ' + data.message, 'error');
        }
    } catch (e) {
        toast('Error: ' + e.message, 'error');
    }
}

async function undoCheckin(apiId) {
    try {
        await fetch(`/admin/api/undo-checkin/${apiId}`, { method: 'POST' });
        toast('Check-in undone', 'success');
        loadStats();
        loadGuests();
    } catch (e) {
        toast('Error: ' + e.message, 'error');
    }
}

async function reprintBadge(apiId) {
    try {
        await fetch(`/admin/api/reprint/${apiId}`, { method: 'POST' });
        toast('Badge reprinting...', 'success');
    } catch (e) {
        toast('Reprint failed: ' + e.message, 'error');
    }
}

async function checkPrinter() {
    try {
        const resp = await fetch('/admin/api/printer-status');
        const data = await resp.json();
        const dot = document.getElementById('printer-dot');
        const label = document.getElementById('printer-label');
        if (data.connected) {
            dot.className = 'status-dot green';
            label.textContent = 'Printer: Connected';
        } else {
            dot.className = 'status-dot red';
            label.textContent = 'Printer: ' + (data.message || 'Not connected');
        }
    } catch (e) {
        document.getElementById('printer-dot').className = 'status-dot red';
        document.getElementById('printer-label').textContent = 'Printer: Error';
    }
}

async function generateQR() {
    const container = document.getElementById('qr-container');
    const img = document.getElementById('qr-image');

    // Use the current server URL as the check-in URL
    const checkinUrl = window.location.origin;
    const qrApiUrl = `https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=${encodeURIComponent(checkinUrl)}`;

    img.src = qrApiUrl;
    container.style.display = 'block';
    toast(`QR code generated for: ${checkinUrl}`, 'success');
}

function toast(message, type = '') {
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
