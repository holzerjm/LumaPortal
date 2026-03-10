// Check-in page state machine
const State = {
    WELCOME: 'screen-welcome',
    CONFIRM: 'screen-confirm',
    SUCCESS: 'screen-success',
    DUPLICATE: 'screen-duplicate',
    NOTFOUND: 'screen-notfound',
};

let currentState = State.WELCOME;
let selectedGuest = null;
let fuse = null;
let guests = [];
let countdownTimer = null;

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

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    initTheme();
    await loadEventInfo();
    await loadGuests();
    setupEventListeners();
});

async function loadEventInfo() {
    try {
        const resp = await fetch('/api/stats');
        const data = await resp.json();
        if (data.event_name) {
            document.getElementById('event-name').textContent = data.event_name;
            document.title = 'Innovate Together - Check-In';
        }
    } catch (e) {
        console.warn('Could not load event info:', e);
    }
}

async function loadGuests() {
    try {
        const resp = await fetch('/api/guests');
        guests = await resp.json();
        // Initialize Fuse.js for client-side fuzzy search
        fuse = new Fuse(guests, {
            keys: [
                { name: 'name', weight: 1.0 },
                { name: 'first_name', weight: 0.8 },
                { name: 'last_name', weight: 0.8 },
                { name: 'email', weight: 0.5 },
                { name: 'company', weight: 0.3 },
            ],
            threshold: 0.4,
            ignoreLocation: true,
            minMatchCharLength: 2,
            includeScore: true,
        });
    } catch (e) {
        console.error('Could not load guests:', e);
    }
}

function setupEventListeners() {
    const input = document.getElementById('search-input');
    let debounceTimer;

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => doSearch(input.value), 300);
    });

    document.getElementById('btn-confirm').addEventListener('click', doCheckIn);
    document.getElementById('btn-back').addEventListener('click', () => showScreen(State.WELCOME));
    document.getElementById('btn-dup-back').addEventListener('click', () => showScreen(State.WELCOME));
    document.getElementById('btn-notfound-back').addEventListener('click', () => showScreen(State.WELCOME));
    document.getElementById('btn-reprint').addEventListener('click', doReprint);
}

function doSearch(query) {
    const resultsEl = document.getElementById('search-results');
    const noResults = document.getElementById('no-results');

    if (!query || query.length < 2 || !fuse) {
        resultsEl.innerHTML = '';
        noResults.classList.add('hidden');
        return;
    }

    const results = fuse.search(query).slice(0, 5);

    if (results.length === 0) {
        resultsEl.innerHTML = '';
        noResults.classList.remove('hidden');
        return;
    }

    noResults.classList.add('hidden');
    resultsEl.innerHTML = results.map(r => {
        const g = r.item;
        const checkedClass = g.checked_in ? 'checked-in' : '';
        const badge = g.checked_in
            ? '<span class="result-badge checked">Checked In</span>'
            : '';
        const detail = [g.company, g.job_title].filter(Boolean).join(' - ');
        return `
            <div class="result-card ${checkedClass}" data-api-id="${g.api_id}">
                <div>
                    <div class="result-name">${escapeHtml(g.name)}</div>
                    ${detail ? `<div class="result-detail">${escapeHtml(detail)}</div>` : ''}
                </div>
                ${badge}
            </div>
        `;
    }).join('');

    // Attach click handlers
    resultsEl.querySelectorAll('.result-card').forEach(card => {
        card.addEventListener('click', () => {
            const apiId = card.dataset.apiId;
            selectedGuest = guests.find(g => g.api_id === apiId);
            if (selectedGuest) showConfirmScreen();
        });
    });
}

function showConfirmScreen() {
    if (!selectedGuest) return;

    document.getElementById('confirm-name').textContent = selectedGuest.name;
    document.getElementById('confirm-company').textContent = selectedGuest.company || '';
    document.getElementById('confirm-title').textContent = selectedGuest.job_title || '';

    showScreen(State.CONFIRM);
}

async function doCheckIn() {
    if (!selectedGuest) return;

    showLoading(true);

    try {
        const resp = await fetch('/api/checkin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_id: selectedGuest.api_id }),
        });
        const data = await resp.json();

        showLoading(false);

        if (data.status === 'success') {
            document.getElementById('success-message').textContent = data.message;
            // Update local cache
            const g = guests.find(g => g.api_id === selectedGuest.api_id);
            if (g) {
                g.checked_in = true;
                g.checked_in_at = data.checked_in_at;
            }
            showScreen(State.SUCCESS);
            startCountdown();
        } else if (data.status === 'duplicate') {
            document.getElementById('duplicate-message').textContent = data.message;
            showScreen(State.DUPLICATE);
        } else if (data.status === 'not_found') {
            showScreen(State.NOTFOUND);
        } else {
            alert('Check-in error: ' + (data.message || 'Unknown error'));
            showScreen(State.WELCOME);
        }
    } catch (e) {
        showLoading(false);
        alert('Network error. Please try again or see event staff.');
        showScreen(State.WELCOME);
    }
}

async function doReprint() {
    if (!selectedGuest) return;
    try {
        await fetch(`/admin/api/reprint/${selectedGuest.api_id}`, { method: 'POST' });
    } catch (e) {
        console.warn('Reprint failed:', e);
    }
    showScreen(State.WELCOME);
}

function startCountdown() {
    let seconds = 5;
    const el = document.getElementById('countdown');
    el.textContent = seconds;

    if (countdownTimer) clearInterval(countdownTimer);
    countdownTimer = setInterval(() => {
        seconds--;
        el.textContent = seconds;
        if (seconds <= 0) {
            clearInterval(countdownTimer);
            showScreen(State.WELCOME);
        }
    }, 1000);
}

function showScreen(screen) {
    if (countdownTimer) clearInterval(countdownTimer);

    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screen).classList.add('active');
    currentState = screen;

    if (screen === State.WELCOME) {
        selectedGuest = null;
        const input = document.getElementById('search-input');
        input.value = '';
        document.getElementById('search-results').innerHTML = '';
        document.getElementById('no-results').classList.add('hidden');
        setTimeout(() => input.focus(), 100);
    }
}

function showLoading(show) {
    document.getElementById('loading').classList.toggle('hidden', !show);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
