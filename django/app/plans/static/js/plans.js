const pendingChangesMap = {};

function getChanges(planId, reqId) {
    const key = `${planId}|${reqId}`;
    if (!pendingChangesMap[key]) {
        pendingChangesMap[key] = new PendingChanges(planId, reqId);
    }
    return pendingChangesMap[key];
}

function getCsrfToken() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
}

async function saveDraft(planId, reqId) {
    const changes = getChanges(planId, reqId);
    try {
        await fetch(`/plans/${planId}/requirements/${reqId}/save-draft/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(changes.toJSON())
        });
        showToast('Draft saved');
    } catch (err) {
        showToast('Error saving draft', 'error');
    }
}

function discardDraft(planId, reqId) {
    getChanges(planId, reqId).clear();
    window.location.reload();
}

async function saveChanges(planId, reqId) {
    const changes = getChanges(planId, reqId);
    if (!changes.hasChanges()) return;
    try {
        const resp = await fetch(`/plans/${planId}/requirements/${reqId}/save-changes/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                changes: changes.toJSON(),
                scope: 'all'
            })
        });
        if (resp.ok) {
            changes.clear();
            showToast('Changes saved');
            window.location.reload();
        } else {
            showToast('Error saving changes', 'error');
        }
    } catch (err) {
        showToast('Error saving changes', 'error');
    }
}

function removeCourse(planId, reqId, identifier) {
    getChanges(planId, reqId).removeCourse(identifier);
}

function toggleExclude(planId, reqId, identifier, currentlyExcluded) {
    getChanges(planId, reqId).modifyCourse(identifier, {
        is_excluded: !currentlyExcluded
    });
}

function showToast(msg, type = 'success') {
    const container = document.getElementById('toast-container') || document.body;
    const colors = {
        success: 'border-green-500 bg-green-50 text-green-800',
        error: 'border-red-500 bg-red-50 text-red-800',
        info: 'border-[#a51c30] bg-[#fde6e6] text-[#a51c30]',
    };
    const icons = {
        success: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>',
        error: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>',
        info: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>',
    };
    const toast = document.createElement('div');
    toast.className = `flex items-center gap-2 px-4 py-3 rounded-lg border-l-4 shadow-md text-sm transition-all duration-300 ${colors[type] || colors.success}`;
    toast.innerHTML = `
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            ${icons[type] || icons.success}
        </svg>
        <span>${msg}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Initialize pending changes UI on page load
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('requirements-container');
    if (!container) return;

    const planId = container.dataset.planId;
    if (!planId) return;

    container.querySelectorAll('[data-req-section]').forEach(section => {
        const reqId = section.dataset.reqSection;
        getChanges(planId, reqId); // loads from sessionStorage and updates UI
    });
});
