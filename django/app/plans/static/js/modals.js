/**
 * AAR Admin Modal Interactions
 * Handles Add Course, Edit Validity, and Requirement modals
 */

const stagedCourses = {};
let currentListCourses = [];

// ============ Add Course Modal ============

function openAddCourseModal(planId, reqId, reqTitle) {
    document.getElementById('acm-plan-id').value = planId;
    document.getElementById('acm-req-id').value = reqId;
    document.getElementById('acm-req-title').textContent = reqTitle;

    clearSearchResults();
    clearStagedCourses();
    document.getElementById('acm-wildcard-input').value = '';
    document.getElementById('acm-wildcard-review').classList.add('hidden');
    document.getElementById('acm-add-wildcards-btn').disabled = true;
    document.getElementById('acm-course-list-select').value = '';
    document.getElementById('acm-list-preview').innerHTML = '<p class="text-sm text-neutral-500 text-center py-4">Select a course list to preview</p>';
    document.getElementById('acm-add-from-list-btn').disabled = true;
    currentListCourses = [];

    HSOverlay.open(document.getElementById('add-course-modal'));
}

// --- Search ---

let searchTimeout = null;

function searchCourses(query) {
    if (searchTimeout) clearTimeout(searchTimeout);

    searchTimeout = setTimeout(async () => {
        const resultsContainer = document.getElementById('acm-search-results');
        if (!query || query.trim().length < 2) {
            resultsContainer.innerHTML = '<p class="text-sm text-neutral-500 text-center py-4">Start typing to search courses</p>';
            return;
        }
        try {
            const resp = await fetch(`/api/courses/search/?q=${encodeURIComponent(query)}`);
            if (!resp.ok) throw new Error('Search failed');
            const data = await resp.json();
            const courses = data.courses || [];
            renderSearchResults(courses);
        } catch (err) {
            console.error('Search error:', err);
            resultsContainer.innerHTML = '<p class="text-sm text-red-500 text-center py-4">Error searching courses</p>';
        }
    }, 300);
}

function renderSearchResults(courses) {
    const container = document.getElementById('acm-search-results');
    if (!courses || courses.length === 0) {
        container.innerHTML = '<p class="text-sm text-neutral-500 text-center py-4">No courses found</p>';
        return;
    }
    container.innerHTML = courses.map(c => `
        <div class="flex items-center justify-between p-2 hover:bg-neutral-50 rounded-lg cursor-pointer"
             onclick="stageCourse('${c.system_id}', '${escapeHtml(c.id)}', '${escapeHtml(c.title)}', '${escapeHtml(c.department)}', ${c.credits})">
            <div class="flex items-center gap-3">
                <span class="px-1.5 py-0.5 bg-neutral-200 text-neutral-600 text-xs font-mono rounded">${c.system_id}</span>
                <div>
                    <p class="text-sm font-medium text-neutral-800">${escapeHtml(c.id)} &mdash; ${escapeHtml(c.title)}</p>
                    <p class="text-xs text-neutral-500">${escapeHtml(c.department)} &middot; ${c.credits} credits</p>
                </div>
            </div>
            <svg class="w-4 h-4 text-neutral-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
        </div>
    `).join('');
}

// --- Staging ---

function stageCourse(systemId, courseId, title, dept, credits) {
    if (stagedCourses[systemId]) return;
    stagedCourses[systemId] = { system_id: systemId, id: courseId, title, department: dept, credits };
    renderStagedCourses();
}

function unstageCourse(systemId) {
    delete stagedCourses[systemId];
    renderStagedCourses();
}

function renderStagedCourses() {
    const container = document.getElementById('acm-staging-container');
    const staged = document.getElementById('acm-staged');
    const btn = document.getElementById('acm-add-staged-btn');
    const keys = Object.keys(stagedCourses);

    if (keys.length === 0) {
        container.classList.add('hidden');
        btn.disabled = true;
        return;
    }

    container.classList.remove('hidden');
    btn.disabled = false;
    staged.innerHTML = keys.map(k => {
        const c = stagedCourses[k];
        return `<span class="inline-flex items-center gap-1 px-2 py-1 badge badge-primary text-sm rounded-lg">
            ${escapeHtml(c.id)}
            <button type="button" onclick="unstageCourse('${k}')" class="hover:text-primary-dark">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
        </span>`;
    }).join('');
}

function clearStagedCourses() {
    Object.keys(stagedCourses).forEach(k => delete stagedCourses[k]);
    const container = document.getElementById('acm-staging-container');
    if (container) container.classList.add('hidden');
    const btn = document.getElementById('acm-add-staged-btn');
    if (btn) btn.disabled = true;
}

function clearSearchResults() {
    const results = document.getElementById('acm-search-results');
    if (results) results.innerHTML = '<p class="text-sm text-neutral-500 text-center py-4">Start typing to search courses</p>';
    const input = document.getElementById('acm-search-input');
    if (input) input.value = '';
}

function addStagedCourses() {
    const planId = document.getElementById('acm-plan-id').value;
    const reqId = document.getElementById('acm-req-id').value;
    if (!planId || !reqId) return;

    const keys = Object.keys(stagedCourses);
    if (keys.length === 0) return;

    keys.forEach(systemId => {
        const courseData = {
            identifier: systemId,
            is_wildcard: false,
            is_excluded: false,
            include_equivalent_courses: false,
            validity_type: 'ALWAYS',
            valid_terms: null
        };
        getChanges(planId, reqId).addCourse(systemId, courseData);
    });

    HSOverlay.close(document.getElementById('add-course-modal'));
    clearStagedCourses();
    showToast(`Added ${keys.length} course(s)`);
}

// --- Wildcards ---

function reviewWildcards() {
    const textarea = document.getElementById('acm-wildcard-input');
    const patterns = textarea.value.split('\n').map(p => p.trim()).filter(p => p.length > 0);
    if (patterns.length === 0) {
        showToast('No patterns entered', 'error');
        return;
    }

    const valid = patterns.filter(p => p.includes('#') || p.includes('*'));
    document.getElementById('acm-valid-count').textContent = valid.length;
    document.getElementById('acm-duplicate-count').textContent = patterns.length - valid.length;
    document.getElementById('acm-wildcard-review').classList.remove('hidden');
    document.getElementById('acm-add-wildcards-btn').disabled = valid.length === 0;
    textarea.dataset.validPatterns = valid.join(',');
}

function addWildcards() {
    const planId = document.getElementById('acm-plan-id').value;
    const reqId = document.getElementById('acm-req-id').value;
    if (!planId || !reqId) return;

    const textarea = document.getElementById('acm-wildcard-input');
    const patterns = (textarea.dataset.validPatterns || '').split(',').filter(p => p.length > 0);
    if (patterns.length === 0) return;

    patterns.forEach(pattern => {
        const courseData = {
            identifier: pattern,
            is_wildcard: true,
            is_excluded: false,
            include_equivalent_courses: false,
            validity_type: 'ALWAYS',
            valid_terms: null
        };
        getChanges(planId, reqId).addCourse(pattern, courseData);
    });

    HSOverlay.close(document.getElementById('add-course-modal'));
    showToast(`Added ${patterns.length} wildcard(s)`);
}

// --- Add From List ---

async function loadCourseList(listId) {
    const preview = document.getElementById('acm-list-preview');
    const btn = document.getElementById('acm-add-from-list-btn');

    if (!listId) {
        preview.innerHTML = '<p class="text-sm text-neutral-500 text-center py-4">Select a course list to preview</p>';
        currentListCourses = [];
        btn.disabled = true;
        return;
    }

    try {
        const resp = await fetch(`/api/course-lists/${listId}/`);
        if (!resp.ok) throw new Error('Failed to load');
        const data = await resp.json();
        currentListCourses = data.courses || [];

        if (currentListCourses.length === 0) {
            preview.innerHTML = '<p class="text-sm text-neutral-500 text-center py-4">No courses in this list</p>';
            btn.disabled = true;
            return;
        }

        preview.innerHTML = currentListCourses.map(c => `
            <div class="flex items-center gap-2 p-2 hover:bg-neutral-50 rounded-lg">
                <span class="px-1.5 py-0.5 bg-neutral-200 text-neutral-600 text-xs font-mono rounded">${c.system_id}</span>
                <span class="text-sm text-neutral-700">${escapeHtml(c.id)}</span>
                <span class="text-xs text-neutral-500">${escapeHtml(c.title)}</span>
            </div>
        `).join('');
        btn.disabled = false;
    } catch (err) {
        preview.innerHTML = '<p class="text-sm text-red-500 text-center py-4">Error loading course list</p>';
        btn.disabled = true;
    }
}

function addFromList() {
    const planId = document.getElementById('acm-plan-id').value;
    const reqId = document.getElementById('acm-req-id').value;
    if (!planId || !reqId || currentListCourses.length === 0) return;

    currentListCourses.forEach(c => {
        const courseData = {
            identifier: c.system_id,
            is_wildcard: false,
            is_excluded: false,
            include_equivalent_courses: false,
            validity_type: 'ALWAYS',
            valid_terms: null
        };
        getChanges(planId, reqId).addCourse(c.system_id, courseData);
    });

    HSOverlay.close(document.getElementById('add-course-modal'));
    showToast(`Added ${currentListCourses.length} course(s) from list`);
}

// ============ Edit Validity Modal ============

function openValidityModal(planId, reqId, identifier, currentValidity, currentTerms, isWildcard) {
    document.getElementById('evm-plan-id').value = planId;
    document.getElementById('evm-req-id').value = reqId;
    document.getElementById('evm-identifier').value = identifier;
    document.getElementById('evm-is-wildcard').value = isWildcard ? 'true' : 'false';
    document.getElementById('evm-course-id').textContent = identifier;

    // Reset
    document.querySelector('input[name="evm-validity-type"][value="ALWAYS"]').checked = true;
    document.getElementById('evm-terms-container').classList.add('hidden');
    document.getElementById('evm-date-container').classList.add('hidden');
    document.querySelectorAll('input[name="evm-terms"]').forEach(cb => cb.checked = false);
    document.getElementById('evm-date-from').value = '';
    document.getElementById('evm-date-to').value = '';

    const equiv = document.getElementById('evm-include-equivalent');
    equiv.disabled = isWildcard;
    equiv.checked = false;

    if (currentValidity) {
        document.querySelectorAll('input[name="evm-validity-type"]').forEach(r => {
            r.checked = r.value === currentValidity;
        });
        onValidityTypeChange(currentValidity);

        if (currentValidity === 'TERMS' && currentTerms) {
            const terms = Array.isArray(currentTerms) ? currentTerms : currentTerms.split(',');
            document.querySelectorAll('input[name="evm-terms"]').forEach(cb => {
                cb.checked = terms.includes(cb.value);
            });
        }
    }

    HSOverlay.open(document.getElementById('edit-validity-modal'));
}

function onValidityTypeChange(type) {
    if (!type) {
        const checked = document.querySelector('input[name="evm-validity-type"]:checked');
        type = checked ? checked.value : 'ALWAYS';
    }
    document.getElementById('evm-terms-container').classList.toggle('hidden', type !== 'TERMS');
    document.getElementById('evm-date-container').classList.toggle('hidden', type !== 'DATE_RANGE');
}

function saveValidity() {
    const planId = document.getElementById('evm-plan-id').value;
    const reqId = document.getElementById('evm-req-id').value;
    const identifier = document.getElementById('evm-identifier').value;
    const isWildcard = document.getElementById('evm-is-wildcard').value === 'true';
    if (!planId || !reqId || !identifier) return;

    const validityType = document.querySelector('input[name="evm-validity-type"]:checked').value;

    let validTerms = null;
    if (validityType === 'TERMS') {
        const selected = [];
        document.querySelectorAll('input[name="evm-terms"]:checked').forEach(cb => selected.push(cb.value));
        validTerms = selected.length > 0 ? selected.join(',') : null;
    }

    const modData = {
        validity_type: validityType,
        valid_terms: validTerms,
        include_equivalent_courses: isWildcard ? false : document.getElementById('evm-include-equivalent').checked
    };

    getChanges(planId, reqId).modifyCourse(identifier, modData);
    HSOverlay.close(document.getElementById('edit-validity-modal'));
    showToast('Validity updated');
}

// ============ Requirement Modal ============

function openAddRequirementModal(planId) {
    document.getElementById('rm-plan-id').value = planId;
    document.getElementById('rm-req-id').value = '';
    document.getElementById('rm-title').textContent = 'Add Requirement';
    document.getElementById('rm-req-title').value = '';
    document.getElementById('rm-req-description').value = '';
    document.getElementById('rm-req-courses-count').value = '';
    document.getElementById('rm-req-units').value = '';
    document.getElementById('rm-req-gpa').value = '';
    HSOverlay.open(document.getElementById('requirement-modal'));
}

function openEditRequirementModal(planId, reqId, title, desc, coursesCount, units, gpa) {
    document.getElementById('rm-plan-id').value = planId;
    document.getElementById('rm-req-id').value = reqId;
    document.getElementById('rm-title').textContent = 'Edit Requirement';
    document.getElementById('rm-req-title').value = title || '';
    document.getElementById('rm-req-description').value = desc || '';
    document.getElementById('rm-req-courses-count').value = coursesCount || '';
    document.getElementById('rm-req-units').value = units || '';
    document.getElementById('rm-req-gpa').value = gpa || '';
    HSOverlay.open(document.getElementById('requirement-modal'));
}

async function saveRequirement() {
    const planId = document.getElementById('rm-plan-id').value;
    const reqId = document.getElementById('rm-req-id').value;
    const title = document.getElementById('rm-req-title').value.trim();
    if (!title) { showToast('Title is required', 'error'); return; }
    if (!planId) { showToast('Missing plan ID', 'error'); return; }

    const formData = {
        title,
        description: document.getElementById('rm-req-description').value.trim(),
        required_courses_count: parseInt(document.getElementById('rm-req-courses-count').value) || 0,
        required_units: parseInt(document.getElementById('rm-req-units').value) || 0,
        minimum_gpa: document.getElementById('rm-req-gpa').value || null
    };

    const isEdit = reqId && reqId.length > 0;
    const url = isEdit
        ? `/plans/${planId}/requirements/${reqId}/edit/`
        : `/plans/${planId}/requirements/add/`;

    try {
        const resp = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify(formData)
        });
        if (!resp.ok) throw new Error('Failed to save requirement');

        HSOverlay.close(document.getElementById('requirement-modal'));
        showToast(isEdit ? 'Requirement updated' : 'Requirement added');
        setTimeout(() => window.location.reload(), 500);
    } catch (err) {
        showToast(err.message || 'Error saving requirement', 'error');
    }
}

// ============ Utility ============

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============ Event Listeners ============

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('acm-search-input');
    if (searchInput) searchInput.addEventListener('keyup', function() { searchCourses(this.value); });

    const addStagedBtn = document.getElementById('acm-add-staged-btn');
    if (addStagedBtn) addStagedBtn.addEventListener('click', addStagedCourses);

    const reviewBtn = document.getElementById('acm-review-wildcards-btn');
    if (reviewBtn) reviewBtn.addEventListener('click', reviewWildcards);

    const addWildBtn = document.getElementById('acm-add-wildcards-btn');
    if (addWildBtn) addWildBtn.addEventListener('click', addWildcards);

    const listSelect = document.getElementById('acm-course-list-select');
    if (listSelect) listSelect.addEventListener('change', function() { loadCourseList(this.value); });

    const addListBtn = document.getElementById('acm-add-from-list-btn');
    if (addListBtn) addListBtn.addEventListener('click', addFromList);

    document.querySelectorAll('input[name="evm-validity-type"]').forEach(r => {
        r.addEventListener('change', function() { onValidityTypeChange(this.value); });
    });

    const saveValBtn = document.getElementById('evm-save-btn');
    if (saveValBtn) saveValBtn.addEventListener('click', saveValidity);

    const saveReqBtn = document.getElementById('rm-save-btn');
    if (saveReqBtn) saveReqBtn.addEventListener('click', saveRequirement);
});
