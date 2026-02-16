let selectedCourse = null;
let searchTimeout = null;

// DOM Elements
const searchInput = document.getElementById('course-search');
const searchResults = document.getElementById('search-results');
const selectedCoursePanel = document.getElementById('selected-course-panel');
const usageResultsPanel = document.getElementById('usage-results-panel');
const usageLoading = document.getElementById('usage-loading');
const usageStats = document.getElementById('usage-stats');
const usageResults = document.getElementById('usage-results');
const usageEmpty = document.getElementById('usage-empty');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupSearchInput();
});

function setupSearchInput() {
    if (!searchInput) return;

    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();

        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }

        if (query.length === 0) {
            hideSearchResults();
            return;
        }

        // Debounce 200ms
        searchTimeout = setTimeout(() => {
            searchCourses(query);
        }, 200);
    });

    // Hide dropdown on blur with delay for click registration
    searchInput.addEventListener('blur', function() {
        setTimeout(() => {
            hideSearchResults();
        }, 200);
    });

    // Prevent blur when clicking on results
    searchResults.addEventListener('mousedown', function(e) {
        e.preventDefault();
    });
}

function searchCourses(query) {
    if (!window.allCourses || window.allCourses.length === 0) {
        hideSearchResults();
        return;
    }

    const lowerQuery = query.toLowerCase();

    const results = window.allCourses.filter(course => {
        return (
            (course.system_id && course.system_id.toLowerCase().includes(lowerQuery)) ||
            (course.id && course.id.toLowerCase().includes(lowerQuery)) ||
            (course.title && course.title.toLowerCase().includes(lowerQuery)) ||
            (course.department && course.department.toLowerCase().includes(lowerQuery))
        );
    }).slice(0, 10);

    if (results.length === 0) {
        hideSearchResults();
        return;
    }

    renderSearchResults(results);
}

function renderSearchResults(results) {
    searchResults.innerHTML = '';

    results.forEach(course => {
        const resultItem = document.createElement('div');
        resultItem.className = 'px-4 py-3 hover:bg-neutral-50 cursor-pointer border-b border-neutral-100 last:border-b-0';
        resultItem.innerHTML = `
            <div class="flex items-center gap-3">
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium badge badge-primary">
                    ${escapeHtml(course.system_id || '')}
                </span>
                <span class="text-sm font-medium text-neutral-900">${escapeHtml(course.id || '')}</span>
                <span class="text-sm text-neutral-600 truncate flex-1">${escapeHtml(course.title || '')}</span>
                <span class="text-xs text-neutral-500">${escapeHtml(course.department || '')}</span>
            </div>
        `;

        resultItem.addEventListener('click', () => {
            selectCourse(course.system_id);
        });

        searchResults.appendChild(resultItem);
    });

    searchResults.classList.remove('hidden');
}

function hideSearchResults() {
    searchResults.classList.add('hidden');
}

function selectCourse(systemId) {
    const course = window.allCourses.find(c => c.system_id === systemId);
    if (!course) return;

    selectedCourse = course;

    // Clear search
    searchInput.value = '';
    hideSearchResults();

    // Show selected course panel
    document.getElementById('selected-system-id').textContent = course.system_id || '';
    document.getElementById('selected-course-id').textContent = course.id || '';
    document.getElementById('selected-course-title').textContent = course.title || '';
    document.getElementById('selected-department').textContent = course.department || '';
    document.getElementById('selected-credits').textContent = course.credits ? `${course.credits} Credits` : '';

    selectedCoursePanel.classList.remove('hidden');

    // Show usage panel with loading state
    usageResultsPanel.classList.remove('hidden');
    usageLoading.classList.remove('hidden');
    usageStats.classList.add('hidden');
    usageResults.innerHTML = '';
    usageEmpty.classList.add('hidden');

    fetchUsage(systemId);
}

async function fetchUsage(systemId) {
    try {
        const response = await fetch(`/lookup/api/courses/${systemId}/usage/`);

        if (!response.ok) {
            throw new Error('Failed to fetch usage data');
        }

        const data = await response.json();
        renderUsage(data.usage || []);
    } catch (error) {
        console.error('Error fetching usage:', error);
        usageLoading.classList.add('hidden');
        usageResults.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                Error loading usage data. Please try again.
            </div>
        `;
    }
}

function renderUsage(usage) {
    usageLoading.classList.add('hidden');

    if (!usage || usage.length === 0) {
        usageEmpty.classList.remove('hidden');
        return;
    }

    // Group by plan_name
    const groupedByPlan = {};
    usage.forEach(item => {
        const planName = item.plan_name || 'Unknown Plan';
        if (!groupedByPlan[planName]) {
            groupedByPlan[planName] = {
                plan_type: item.plan_type,
                requirements: []
            };
        }
        groupedByPlan[planName].requirements.push(item);
    });

    const planCount = Object.keys(groupedByPlan).length;
    const requirementCount = usage.length;

    // Update stats
    document.getElementById('stats-text').textContent = `Used in ${planCount} plan(s), ${requirementCount} requirement(s)`;
    usageStats.classList.remove('hidden');

    // Render results
    usageResults.innerHTML = '';

    Object.entries(groupedByPlan).forEach(([planName, planData]) => {
        const planCard = document.createElement('div');
        planCard.className = 'bg-white rounded-lg border border-neutral-200 overflow-hidden';

        const planHeader = document.createElement('div');
        planHeader.className = 'bg-neutral-50 px-4 py-3 border-b border-neutral-200 flex items-center justify-between';
        planHeader.innerHTML = `
            <h3 class="font-semibold text-neutral-900">${escapeHtml(planName)}</h3>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium badge badge-primary">
                ${escapeHtml(planData.plan_type || 'Plan')}
            </span>
        `;
        planCard.appendChild(planHeader);

        const tableContainer = document.createElement('div');
        tableContainer.className = 'overflow-x-auto';

        const table = document.createElement('table');
        table.className = 'min-w-full divide-y divide-neutral-200';
        table.innerHTML = `
            <thead class="bg-neutral-50">
                <tr>
                    <th class="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">Requirement</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">Matched By</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">Status</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-neutral-200">
                ${planData.requirements.map(req => `
                    <tr>
                        <td class="px-4 py-3 text-sm text-neutral-900">${escapeHtml(req.requirement_title || '')}</td>
                        <td class="px-4 py-3 text-sm text-neutral-600 font-mono">${escapeHtml(req.matched_by || '')}</td>
                        <td class="px-4 py-3">
                            ${req.is_excluded
                                ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 line-through">Excluded</span>'
                                : '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Active</span>'
                            }
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        `;

        tableContainer.appendChild(table);
        planCard.appendChild(tableContainer);
        usageResults.appendChild(planCard);
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
