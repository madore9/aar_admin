// State
let batchResults = [];
let selectedPlanId = null;
let selectedReqId = null;
let existingIdentifiers = [];
let importMode = 'catalog';
let resolvingIndex = -1;
let batchStagedCourses = [];
let requirementsData = {};

// --- Target Selection ---

async function onPlanSelect(planId) {
    selectedPlanId = planId;
    const reqSelect = document.getElementById('batch-req-select');

    if (!planId) {
        reqSelect.innerHTML = '<option value="">Select a plan first...</option>';
        reqSelect.disabled = true;
        return;
    }

    try {
        const resp = await fetch(`/batch/api/batch/plan/${planId}/requirements/`);
        if (!resp.ok) throw new Error('Failed');
        const data = await resp.json();
        requirementsData = {};

        reqSelect.innerHTML = '<option value="">Select a requirement...</option>';
        data.requirements.forEach(req => {
            requirementsData[req.id] = req;
            const opt = document.createElement('option');
            opt.value = req.id;
            opt.textContent = req.title;
            reqSelect.appendChild(opt);
        });
        reqSelect.disabled = false;
    } catch (err) {
        console.error('Error loading requirements:', err);
        showBatchToast('Failed to load requirements', 'error');
    }
}

function onReqSelect(reqId) {
    selectedReqId = reqId;
    existingIdentifiers = (reqId && requirementsData[reqId])
        ? requirementsData[reqId].existing_identifiers || []
        : [];
}

// --- Input Handling ---

function handleFileUpload(file) {
    if (!file) return;
    const ext = file.name.toLowerCase();
    if (!ext.endsWith('.txt') && !ext.endsWith('.csv')) {
        showBatchToast('Please upload a .txt or .csv file', 'error');
        return;
    }
    const reader = new FileReader();
    reader.onload = e => {
        document.getElementById('batch-text-input').value = e.target.result;
        showBatchToast('File loaded');
    };
    reader.readAsText(file);
}

function downloadTemplate() {
    const header = importMode === 'catalog' ? 'Catalog Number' : 'Course ID';
    const samples = importMode === 'catalog' ? 'CS50\nCS124\nMATH21a' : '100201\n100204\n100210';
    const blob = new Blob([header + '\n' + samples], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `batch_template_${importMode}.csv`;
    a.click();
}

async function validateInput() {
    if (!selectedPlanId) { showBatchToast('Please select a plan', 'error'); return; }
    if (!selectedReqId) { showBatchToast('Please select a requirement', 'error'); return; }

    const text = document.getElementById('batch-text-input').value.trim();
    if (!text) { showBatchToast('Please enter course identifiers', 'error'); return; }

    let identifiers = text.split(/[\n,]/).map(s => s.trim()).filter(s => s.length > 0);
    // Strip header row if it looks like text-only
    if (identifiers.length > 1 && /^[a-zA-Z\s]+$/.test(identifiers[0])) {
        identifiers = identifiers.slice(1);
    }
    identifiers = [...new Set(identifiers)];
    if (identifiers.length === 0) { showBatchToast('No valid identifiers', 'error'); return; }

    try {
        const resp = await fetch('/batch/api/batch/validate/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getBatchCsrf() },
            body: JSON.stringify({ identifiers, import_mode: importMode, existing_identifiers: existingIdentifiers })
        });
        if (!resp.ok) throw new Error('Validation failed');
        const data = await resp.json();
        batchResults = data.results;
        renderResults();
        document.getElementById('batch-results').classList.remove('hidden');

        const valid = batchResults.filter(r => r.status === 'EXACT_MATCH' || r.status === 'RESOLVED').length;
        showBatchToast(`Validation complete: ${valid} matches found`);
    } catch (err) {
        console.error('Validation error:', err);
        showBatchToast('Failed to validate', 'error');
    }
}

// --- Results ---

function renderResults() {
    const total = batchResults.length;
    const matched = batchResults.filter(r => r.status === 'EXACT_MATCH' || r.status === 'RESOLVED').length;
    const duplicates = batchResults.filter(r => r.status === 'DUPLICATE').length;
    const needsReview = batchResults.filter(r => r.status === 'MULTIPLE_MATCHES' || r.status === 'NO_MATCH').length;

    document.getElementById('stat-total').textContent = total;
    document.getElementById('stat-matched').textContent = matched;
    document.getElementById('stat-duplicates').textContent = duplicates;
    document.getElementById('stat-needs-review').textContent = needsReview;

    const tbody = document.getElementById('batch-results-body');
    tbody.innerHTML = '';

    batchResults.forEach((result, i) => {
        const row = document.createElement('tr');
        let courseInfo = '&mdash;';

        if (result.selected && result.selected.length > 0) {
            const c = result.selected[0];
            courseInfo = `<span class="font-mono text-xs bg-neutral-200 px-1 py-0.5 rounded">${c.system_id}</span> ${escBatch(c.id)} &mdash; ${escBatch(c.title)}`;
        } else if (result.candidates && result.candidates.length > 0) {
            courseInfo = `${result.candidates.length} candidate(s)`;
        }

        let actions = '';
        if (result.status === 'MULTIPLE_MATCHES') {
            actions += `<button type="button" onclick="openResolveModal(${i})" class="text-[#a51c30] hover:underline text-sm font-medium">Resolve</button> `;
        }
        actions += `<button type="button" onclick="removeResult(${i})" class="text-neutral-400 hover:text-red-500 text-sm">Remove</button>`;

        row.innerHTML = `
            <td class="px-4 py-3 text-sm text-neutral-900 font-mono">${escBatch(result.input)}</td>
            <td class="px-4 py-3">${getStatusBadge(result.status)}</td>
            <td class="px-4 py-3 text-sm text-neutral-600">${courseInfo}</td>
            <td class="px-4 py-3">${actions}</td>
        `;
        tbody.appendChild(row);
    });

    const btn = document.getElementById('batch-add-valid');
    btn.textContent = `Add ${matched} Valid Matches`;
    btn.disabled = matched === 0;
}

function getStatusBadge(status) {
    const map = {
        'EXACT_MATCH': ['bg-green-100 text-green-700', 'Match'],
        'RESOLVED': ['bg-green-100 text-green-700', 'Resolved'],
        'DUPLICATE': ['bg-amber-100 text-amber-700', 'Duplicate'],
        'MULTIPLE_MATCHES': ['bg-blue-100 text-blue-700', 'Multiple'],
        'NO_MATCH': ['bg-red-100 text-red-700', 'No Match'],
    };
    const [cls, label] = map[status] || map['NO_MATCH'];
    return `<span class="${cls} px-2 py-1 rounded-full text-xs font-medium">${label}</span>`;
}

function removeResult(i) {
    batchResults.splice(i, 1);
    renderResults();
}

// --- Resolution Modal ---

function openResolveModal(index) {
    resolvingIndex = index;
    const result = batchResults[index];
    document.getElementById('brm-input').textContent = result.input;

    const container = document.getElementById('batch-resolve-candidates');
    container.innerHTML = result.candidates.map(c => {
        const isDup = existingIdentifiers.includes(c.system_id);
        return `<div class="flex items-start gap-3 p-3 border border-neutral-200 rounded-lg hover:bg-neutral-50">
            <input type="checkbox" value="${c.system_id}" class="mt-1 h-4 w-4 text-[#a51c30] focus:ring-[#a51c30] border-neutral-300 rounded">
            <div class="flex-1">
                <div class="flex items-center gap-2">
                    <span class="font-mono text-sm">${c.system_id}</span>
                    <span class="font-medium text-neutral-900">${escBatch(c.id)}</span>
                    ${isDup ? '<span class="bg-amber-100 text-amber-700 px-2 py-0.5 rounded text-xs">Already exists</span>' : ''}
                </div>
                <p class="text-sm text-neutral-600">${escBatch(c.title)}</p>
            </div>
        </div>`;
    }).join('');

    document.getElementById('batch-resolve-modal').classList.remove('hidden');
}

function confirmResolution() {
    const checked = document.querySelectorAll('#batch-resolve-candidates input[type="checkbox"]:checked');
    const ids = Array.from(checked).map(cb => cb.value);
    if (ids.length === 0) { showBatchToast('Select at least one', 'error'); return; }

    const result = batchResults[resolvingIndex];
    result.selected = result.candidates.filter(c => ids.includes(c.system_id));
    const allDup = result.selected.every(c => existingIdentifiers.includes(c.system_id));
    result.status = allDup ? 'DUPLICATE' : 'RESOLVED';

    document.getElementById('batch-resolve-modal').classList.add('hidden');
    renderResults();
    showBatchToast('Selection confirmed');
}

// --- Save ---

async function addValidMatches() {
    if (!selectedPlanId || !selectedReqId) { showBatchToast('Select plan and requirement', 'error'); return; }

    const valid = batchResults.filter(r => r.status === 'EXACT_MATCH' || r.status === 'RESOLVED');
    if (valid.length === 0) { showBatchToast('No valid matches', 'error'); return; }

    const additions = {};
    valid.forEach(r => {
        (r.selected || []).forEach(c => {
            if (!existingIdentifiers.includes(c.system_id)) {
                additions[c.system_id] = {
                    identifier: c.system_id,
                    is_wildcard: false,
                    is_excluded: false,
                    include_equivalent_courses: false,
                    validity_type: 'ALWAYS',
                    valid_terms: null
                };
            }
        });
    });

    if (Object.keys(additions).length === 0) { showBatchToast('All already in requirement', 'error'); return; }

    try {
        const resp = await fetch(`/plans/${selectedPlanId}/requirements/${selectedReqId}/save-changes/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getBatchCsrf() },
            body: JSON.stringify({ changes: { additions, removals: [], modifications: {} }, scope: 'all' })
        });
        if (!resp.ok) throw new Error('Save failed');

        showBatchToast(`Added ${Object.keys(additions).length} courses`);
        batchResults = [];
        document.getElementById('batch-results').classList.add('hidden');
        document.getElementById('batch-text-input').value = '';

        if (requirementsData[selectedReqId]) {
            requirementsData[selectedReqId].existing_identifiers.push(...Object.keys(additions));
            existingIdentifiers = requirementsData[selectedReqId].existing_identifiers;
        }
    } catch (err) {
        showBatchToast('Failed to save', 'error');
    }
}

// --- Catalog Search ---

function batchSearchCourses(query) {
    const container = document.getElementById('batch-search-results');
    if (!query || query.length < 2) {
        container.innerHTML = '<div class="p-4 text-sm text-neutral-500 text-center">Search for courses to stage</div>';
        return;
    }
    const courses = window.allCourses || [];
    const q = query.toLowerCase();
    const filtered = courses.filter(c =>
        `${c.system_id} ${c.id} ${c.title} ${c.department}`.toLowerCase().includes(q)
    ).slice(0, 20);

    if (filtered.length === 0) {
        container.innerHTML = '<div class="p-4 text-sm text-neutral-500 text-center">No courses found</div>';
        return;
    }
    container.innerHTML = filtered.map(c => `
        <div class="p-3 border-b border-neutral-100 hover:bg-neutral-50 cursor-pointer"
             onclick="batchStageCourse('${c.system_id}','${escBatch(c.id)}','${escBatch(c.title)}')">
            <span class="font-mono text-xs bg-neutral-200 px-1 py-0.5 rounded">${c.system_id}</span>
            <span class="ml-2 font-medium text-neutral-900">${escBatch(c.id)}</span>
            <span class="text-neutral-500">&mdash; ${escBatch(c.title)}</span>
        </div>
    `).join('');
}

function batchStageCourse(systemId, id, title) {
    if (batchStagedCourses.some(c => c.system_id === systemId)) return;
    batchStagedCourses.push({ system_id: systemId, id, title });
    renderBatchStaged();
}

function batchUnstageCourse(i) {
    batchStagedCourses.splice(i, 1);
    renderBatchStaged();
}

function renderBatchStaged() {
    const container = document.getElementById('batch-staged-courses');
    if (batchStagedCourses.length === 0) {
        container.innerHTML = '<span class="text-sm text-neutral-400">No courses staged</span>';
        return;
    }
    container.innerHTML = batchStagedCourses.map((c, i) => `
        <span class="inline-flex items-center gap-1 bg-[#fde6e6] text-[#a51c30] px-2 py-1 rounded text-sm">
            ${escBatch(c.id)}
            <button type="button" onclick="batchUnstageCourse(${i})" class="hover:text-[#801b30]">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
        </span>
    `).join('');
}

// --- Utilities ---

function getBatchCsrf() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
}

function escBatch(t) {
    const d = document.createElement('div');
    d.textContent = t;
    return d.innerHTML;
}

function showBatchToast(msg, type = 'success') {
    const existing = document.querySelector('.batch-toast');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.className = `batch-toast fixed bottom-4 right-4 px-4 py-2 rounded-lg text-white text-sm z-50 ${type === 'error' ? 'bg-red-600' : 'bg-green-600'}`;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// --- Event Listeners ---

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('batch-plan-select').addEventListener('change', e => onPlanSelect(e.target.value));
    document.getElementById('batch-req-select').addEventListener('change', e => onReqSelect(e.target.value));

    document.querySelectorAll('input[name="import-mode"]').forEach(r => {
        r.addEventListener('change', e => { importMode = e.target.value; });
    });

    // File drag/drop
    const dropZone = document.getElementById('batch-file-drop-zone');
    const fileInput = document.getElementById('batch-file-input');

    dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('border-[#a51c30]'); });
    dropZone.addEventListener('dragleave', e => { e.preventDefault(); dropZone.classList.remove('border-[#a51c30]'); });
    dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('border-[#a51c30]'); handleFileUpload(e.dataTransfer.files[0]); });
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', e => handleFileUpload(e.target.files[0]));

    document.getElementById('batch-validate-btn').addEventListener('click', validateInput);
    document.getElementById('batch-download-template').addEventListener('click', downloadTemplate);
    document.getElementById('batch-add-valid').addEventListener('click', addValidMatches);
    document.getElementById('batch-reset').addEventListener('click', () => {
        batchResults = [];
        document.getElementById('batch-results').classList.add('hidden');
        document.getElementById('batch-text-input').value = '';
    });

    // Catalog search
    let batchSearchTimeout;
    document.getElementById('batch-catalog-search').addEventListener('input', e => {
        clearTimeout(batchSearchTimeout);
        batchSearchTimeout = setTimeout(() => batchSearchCourses(e.target.value), 300);
    });

    document.getElementById('batch-stage-validate').addEventListener('click', () => {
        if (batchStagedCourses.length === 0) { showBatchToast('No courses staged', 'error'); return; }
        const ids = batchStagedCourses.map(c => importMode === 'id' ? c.system_id : c.id);
        document.getElementById('batch-text-input').value = ids.join('\n');
        showBatchToast(`${batchStagedCourses.length} courses staged for validation`);
        batchStagedCourses = [];
        renderBatchStaged();
    });

    // Resolution modal
    const closeModal = () => document.getElementById('batch-resolve-modal').classList.add('hidden');
    document.getElementById('batch-resolve-close').addEventListener('click', closeModal);
    document.getElementById('batch-resolve-cancel').addEventListener('click', closeModal);
    document.getElementById('batch-resolve-confirm').addEventListener('click', confirmResolution);
    document.getElementById('batch-resolve-modal').addEventListener('click', e => {
        if (e.target === e.currentTarget) closeModal();
    });
});

// Global exports for inline onclick handlers
window.openResolveModal = openResolveModal;
window.removeResult = removeResult;
window.batchStageCourse = batchStageCourse;
window.batchUnstageCourse = batchUnstageCourse;
