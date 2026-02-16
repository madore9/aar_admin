# AAR Admin — Bug Audit Report v1

**Date:** 2026-02-14
**Scope:** Full codebase audit of `aar_admin_django/` (Django + FastAPI)
**Total Issues:** 27 (7 Critical, 8 High, 9 Medium, 3 Low)

---

## Summary

| Severity | Count | Categories |
|----------|-------|-----------|
| CRITICAL | 7 | RBAC bypass, XSS, secrets exposure, async mismatch |
| HIGH | 8 | Error handling, race conditions, injection, missing validation |
| MEDIUM | 9 | Null checks, RBAC gaps, input validation, rate limiting |
| LOW | 3 | CSS maintainability, UX polish, error message leakage |

---

## Priority Fix Order

1. **#6 + #7** — SECRET_KEY and DEBUG hardcoded (settings.py:8-10)
2. **#1** — RBAC bypass on plan_list/plan_detail (plan_views.py:62-85)
3. **#3 + #4** — XSS in onclick handlers (requirement_section.html, course_row.html)
4. **#2** — Async/sync mismatch in require_admin (plan_views.py:15-22)
5. **#9** — Unhandled exceptions in api_client.py (all functions)
6. **#15** — JSON parsing without try/except (plan_views.py:117,135,152,169)
7. **#12 + #13** — CSV export RBAC + filename sanitization (plan_views.py:190-221)
8. **#20 + #23** — Missing RBAC on search + course list endpoints
9. **#11** — PendingChanges.addCourse race condition (pending-changes.js:31-38)
10. **#17** — innerHTML XSS risk in modals.js (modals.js:61-75)

---

## CRITICAL

### Bug #1: RBAC Bypass — plan_list and plan_detail Have No Role Check

**File:** `django/app/plans/views/plan_views.py` lines 62-85
**Impact:** Any unauthenticated/unauthorized user can view all plans and their full requirement/course details.

**Problem:**
```python
# Line 62 — NO @require_admin decorator
async def plan_list(request):
    search_query = request.GET.get('q', '')
    plans = await get_plans(search_query if search_query else None)
    ...

# Line 73 — NO @require_admin decorator
async def plan_detail(request, plan_id):
    plan = await get_plan_with_course_info(plan_id)
    ...
```

**Fix:** Add `@require_admin` decorator to both views:
```python
@require_admin
async def plan_list(request):
    ...

@require_admin
async def plan_detail(request, plan_id):
    ...
```

**Note:** If DEPT_USER should have read access, create a separate `@require_authenticated` decorator that only blocks anonymous users, and keep `@require_admin` for write operations.

---

### Bug #2: Async/Sync Mismatch in require_admin Decorator

**File:** `django/app/plans/views/plan_views.py` lines 15-22
**Impact:** Decorator always wraps with `async def` and uses `await`, but would crash if applied to a sync view.

**Problem:**
```python
def require_admin(view_func):
    @wraps(view_func)
    async def wrapper(request, *args, **kwargs):
        if request.session.get('user_role', 'DEPT_USER') != 'ADMIN_USER':
            return JsonResponse({'error': 'Admin access required'}, status=403)
        return await view_func(request, *args, **kwargs)  # Assumes view_func is async
    return wrapper
```

**Fix:** Handle both sync and async views:
```python
import asyncio

def require_admin(view_func):
    @wraps(view_func)
    async def wrapper(request, *args, **kwargs):
        if request.session.get('user_role', 'DEPT_USER') != 'ADMIN_USER':
            return JsonResponse({'error': 'Admin access required'}, status=403)
        if asyncio.iscoroutinefunction(view_func):
            return await view_func(request, *args, **kwargs)
        return view_func(request, *args, **kwargs)
    return wrapper
```

---

### Bug #3: XSS in requirement_section.html onclick Handlers

**File:** `django/app/plans/templates/plans/requirement_section.html` lines 12, 23
**Impact:** If `plan.id` or `requirement.id` contains quotes or JS, arbitrary JavaScript executes.

**Problem:**
```html
<!-- Line 12 -->
onclick="openEditRequirementModal('{{ plan.id }}', '{{ requirement.id }}', '{{ requirement.title|escapejs }}', ...)"

<!-- Line 23 -->
onclick="openAddCourseModal('{{ plan.id }}', '{{ requirement.id }}', '{{ requirement.title|escapejs }}')"
```

`{{ plan.id }}` and `{{ requirement.id }}` are NOT escaped with `|escapejs`. If an ID contains `'`, `"`, or `\`, the handler breaks or injects JS.

**Fix:** Use data attributes instead of inline handlers:
```html
<!-- Line 12 — replace onclick with data attributes -->
<button type="button"
        data-action="edit-requirement"
        data-plan-id="{{ plan.id }}"
        data-req-id="{{ requirement.id }}"
        data-req-title="{{ requirement.title }}"
        data-req-desc="{{ requirement.description }}"
        data-req-courses="{{ requirement.required_courses_count|default:'0' }}"
        data-req-units="{{ requirement.required_units|default:'0' }}"
        data-req-gpa="{{ requirement.minimum_gpa|default_if_none:'' }}"
        class="text-neutral-400 hover:text-[#a51c30] transition-colors">
```

Then bind in JS:
```javascript
document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action="edit-requirement"]');
    if (btn) {
        openEditRequirementModal(
            btn.dataset.planId, btn.dataset.reqId, btn.dataset.reqTitle,
            btn.dataset.reqDesc, btn.dataset.reqCourses, btn.dataset.reqUnits,
            btn.dataset.reqGpa
        );
    }
});
```

---

### Bug #4: XSS in course_row.html onclick Handlers (3 Handlers)

**File:** `django/app/plans/templates/plans/course_row.html` lines 54, 64, 72
**Impact:** Same as #3 — `course.identifier`, `plan.id`, `requirement.id` are unescaped in JS context.

**Problem:**
```html
<!-- Line 54 -->
onclick="openValidityModal('{{ plan.id }}', '{{ requirement.id }}', '{{ course.identifier }}', '{{ course.validity_type }}', '{{ course.valid_terms|default_if_none:"" }}', {{ course.is_wildcard|yesno:'true,false' }})"

<!-- Line 64 -->
onclick="toggleExclude('{{ plan.id }}', '{{ requirement.id }}', '{{ course.identifier }}', {{ course.is_excluded|yesno:'true,false' }})"

<!-- Line 72 -->
onclick="removeCourse('{{ plan.id }}', '{{ requirement.id }}', '{{ course.identifier }}')"
```

**Fix:** Same pattern as #3 — use data attributes:
```html
<button type="button"
        data-action="edit-validity"
        data-plan-id="{{ plan.id }}"
        data-req-id="{{ requirement.id }}"
        data-identifier="{{ course.identifier }}"
        data-validity-type="{{ course.validity_type }}"
        data-valid-terms="{{ course.valid_terms|default_if_none:'' }}"
        data-is-wildcard="{{ course.is_wildcard|yesno:'true,false' }}"
        class="p-1 text-neutral-400 hover:text-[#a51c30] transition-colors">
```

Repeat for toggleExclude and removeCourse buttons with `data-action="toggle-exclude"` and `data-action="remove-course"`.

---

### Bug #5: CSRF Token Fragility

**File:** `django/app/plans/templates/plans/plan_detail.html` line 52
**Impact:** If the bare `{% csrf_token %}` hidden input is not found, all AJAX POST requests fail silently with 403.

**Problem:**
```html
{% csrf_token %}  <!-- Renders as hidden input outside any form -->
```

```javascript
// plans.js line 12
function getCsrfToken() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';  // Returns empty string if not found — fails silently
}
```

**Fix:** Add validation and a fallback:
```javascript
function getCsrfToken() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!el || !el.value) {
        console.error('CSRF token not found — POST requests will fail');
    }
    return el ? el.value : '';
}
```

Also consider reading from the `csrftoken` cookie as a fallback (Django sets this cookie when `{% csrf_token %}` is used):
```javascript
function getCsrfToken() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    if (el && el.value) return el.value;
    // Fallback to cookie
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}
```

---

### Bug #6: SECRET_KEY Hardcoded

**File:** `django/app/aar_admin/settings.py` line 8
**Impact:** Anyone with source code access can forge session cookies, CSRF tokens, and password reset links.

**Problem:**
```python
SECRET_KEY = 'django-insecure-aar-admin-dev-key-change-in-production'
```

**Fix:**
```python
import os
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-key-DO-NOT-USE-IN-PROD')
if not DEBUG and 'insecure' in SECRET_KEY:
    raise ValueError("Set DJANGO_SECRET_KEY environment variable for production")
```

---

### Bug #7: DEBUG=True Hardcoded

**File:** `django/app/aar_admin/settings.py` line 10
**Impact:** In production, exposes stack traces, source code, environment variables, and SQL queries to any user who triggers a 500 error.

**Problem:**
```python
DEBUG = True
```

**Fix:**
```python
import os
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')
```

---

## HIGH

### Bug #8: ALLOWED_HOSTS Wildcard

**File:** `django/app/aar_admin/settings.py` line 12
**Impact:** Enables Host header injection attacks. Attacker can craft URLs that poison password reset emails, caches, or generate malicious links.

**Problem:**
```python
ALLOWED_HOSTS = ['*']
```

**Fix:**
```python
import os
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
```

---

### Bug #9: Unhandled Exceptions in api_client.py

**File:** `django/app/plans/services/api_client.py` lines 7-37
**Impact:** If FastAPI is down, returns an unhandled `httpx.ConnectError` or `httpx.HTTPStatusError`, causing Django to return 500 with a stack trace (especially bad with DEBUG=True).

**Problem:**
```python
async def api_get(path: str, params: dict = None) -> dict | list | None:
    async with httpx.AsyncClient(base_url=AAR_API_URL, timeout=20.0) as client:
        response = await client.get(f"/aar{path}", params=params, follow_redirects=True)
        response.raise_for_status()  # Throws unhandled exception
        ...
```

All four functions (`api_get`, `api_post`, `api_put`, `api_delete`) have the same issue.

**Fix:**
```python
import logging

logger = logging.getLogger(__name__)

async def api_get(path: str, params: dict = None) -> dict | list | None:
    try:
        async with httpx.AsyncClient(base_url=AAR_API_URL, timeout=10.0) as client:
            response = await client.get(f"/aar{path}", params=params, follow_redirects=True)
            response.raise_for_status()
            if response.content:
                return response.json()
            return None
    except httpx.HTTPStatusError as e:
        logger.error(f"API HTTP error for GET {path}: {e.response.status_code}")
        raise
    except httpx.ConnectError:
        logger.error(f"API connection failed for GET {path} — is FastAPI running?")
        return None
    except httpx.TimeoutException:
        logger.error(f"API timeout for GET {path}")
        return None
```

---

### Bug #10: 20s Timeout with No Backoff

**File:** `django/app/plans/services/api_client.py` lines 8, 17, 26, 35
**Impact:** A slow FastAPI response blocks the Django worker for up to 20 seconds per request. Under load, this exhausts all workers.

**Problem:**
```python
async with httpx.AsyncClient(base_url=AAR_API_URL, timeout=20.0) as client:
```

**Fix:** Reduce timeout to 5s and add retry with backoff for transient failures:
```python
import asyncio

async def _api_request(method, path, **kwargs):
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(base_url=AAR_API_URL, timeout=5.0) as client:
                response = await getattr(client, method)(f"/aar{path}", **kwargs)
                response.raise_for_status()
                if response.content:
                    return response.json()
                return None
        except httpx.TimeoutException:
            if attempt < max_retries:
                await asyncio.sleep(0.5 * (2 ** attempt))
            else:
                raise
```

---

### Bug #11: Race Condition in PendingChanges.addCourse

**File:** `django/app/plans/static/js/pending-changes.js` lines 31-38
**Impact:** If a course is added, then removed, then added again — the second add only removes it from the removals list but does NOT add it to additions. The course disappears.

**Problem:**
```javascript
addCourse(identifier, courseData) {
    const idx = this.removals.indexOf(identifier);
    if (idx !== -1) {
        this.removals.splice(idx, 1);   // Removes from removals
        // BUG: Falls through without adding to additions
    } else {
        this.additions[identifier] = courseData;  // Only adds if NOT in removals
    }
    this._save();
}
```

**Fix:**
```javascript
addCourse(identifier, courseData) {
    // Always remove from removals if present
    const idx = this.removals.indexOf(identifier);
    if (idx !== -1) {
        this.removals.splice(idx, 1);
    }
    // Always add to additions
    this.additions[identifier] = courseData;
    this._save();
}
```

---

### Bug #12: Missing RBAC on export_plan_csv

**File:** `django/app/plans/views/plan_views.py` lines 190-221
**Impact:** Any user (including anonymous) can export any plan's course data as CSV.

**Problem:**
```python
async def export_plan_csv(request, plan_id):  # NO @require_admin
    plan = await get_plan_with_course_info(plan_id)
    ...
```

**Fix:**
```python
@require_admin
async def export_plan_csv(request, plan_id):
    ...
```

---

### Bug #13: Unsafe Filename in CSV Content-Disposition

**File:** `django/app/plans/views/plan_views.py` lines 219-220
**Impact:** Plan names containing quotes, slashes, or non-ASCII characters break the HTTP header or enable header injection.

**Problem:**
```python
safe_name = plan.get('name', 'plan').replace(' ', '_')
response['Content-Disposition'] = f'attachment; filename="{safe_name}_Requirements.csv"'
```

If `plan.name = 'plan"; evil-header: injected'`, the Content-Disposition header is corrupted.

**Fix:**
```python
import re
import unicodedata

raw_name = plan.get('name', 'plan')
safe_name = unicodedata.normalize('NFKD', raw_name)
safe_name = re.sub(r'[^\w\s-]', '', safe_name).strip()
safe_name = re.sub(r'[-\s]+', '_', safe_name)
if not safe_name:
    safe_name = 'plan'
response['Content-Disposition'] = f'attachment; filename="{safe_name}_Requirements.csv"'
```

---

### Bug #14: No Input Length Validation on Course Search

**File:** `django/app/plans/views/plan_views.py` lines 96-102
**File:** `fastapi/app/routers/courses.py`
**Impact:** A 1MB search query gets passed to SQLite LIKE queries, causing excessive CPU/memory.

**Problem:**
```python
async def api_search_courses(request):
    q = request.GET.get('q', '')
    if len(q) < 2:
        return JsonResponse({'courses': []})
    courses_data = await get_courses(q)  # No upper bound on query length
```

**Fix:**
```python
async def api_search_courses(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'courses': []})
    if len(q) > 200:
        return JsonResponse({'error': 'Search query too long'}, status=400)
    courses_data = await get_courses(q)
```

---

### Bug #15: JSON Parsing Without try/except

**File:** `django/app/plans/views/plan_views.py` lines 117, 135, 152, 169
**Impact:** Malformed JSON in POST body returns 500 instead of 400.

**Problem:**
```python
# Line 117 (api_add_requirement)
data = json.loads(request.body)  # No error handling

# Line 135 (api_edit_requirement)
data = json.loads(request.body)  # No error handling

# Line 152 (api_save_draft)
data = json.loads(request.body)  # No error handling

# Line 169 (api_save_changes)
data = json.loads(request.body)  # No error handling
```

**Fix:** Wrap each in try/except:
```python
try:
    data = json.loads(request.body)
except (json.JSONDecodeError, ValueError):
    return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
```

Or create a helper:
```python
def parse_json_body(request):
    try:
        return json.loads(request.body), None
    except (json.JSONDecodeError, ValueError):
        return None, JsonResponse({'error': 'Invalid JSON'}, status=400)

# Usage:
data, err = parse_json_body(request)
if err:
    return err
```

---

## MEDIUM

### Bug #16: Missing Null Checks in modals.js DOM Manipulation

**File:** `django/app/plans/static/js/modals.js` lines 91-101
**Impact:** If modal HTML elements are missing (e.g., page partially loaded), JavaScript errors crash the UI.

**Problem:**
```javascript
function renderStagedCourses() {
    const container = document.getElementById('acm-staging-container');  // Could be null
    const staged = document.getElementById('acm-staged');               // Could be null
    const btn = document.getElementById('acm-add-staged-btn');          // Could be null
    const keys = Object.keys(stagedCourses);

    if (keys.length === 0) {
        container.classList.add('hidden');  // TypeError if null
        btn.disabled = true;               // TypeError if null
        return;
    }
```

**Fix:**
```javascript
function renderStagedCourses() {
    const container = document.getElementById('acm-staging-container');
    const staged = document.getElementById('acm-staged');
    const btn = document.getElementById('acm-add-staged-btn');
    if (!container || !staged || !btn) return;
    ...
}
```

---

### Bug #17: XSS Risk in modals.js innerHTML with Template Literals

**File:** `django/app/plans/static/js/modals.js` lines 61-75
**Impact:** `escapeHtml()` is called on some fields but `c.system_id` and `c.credits` are NOT escaped. If course data contains HTML, XSS is possible.

**Problem:**
```javascript
container.innerHTML = courses.map(c => `
    <div class="..." onclick="stageCourse('${c.system_id}', '${escapeHtml(c.id)}', ...)">
        <span class="...">${c.system_id}</span>  <!-- NOT ESCAPED -->
        <p class="...">${escapeHtml(c.id)} &mdash; ${escapeHtml(c.title)}</p>
        <p class="...">${escapeHtml(c.department)} &middot; ${c.credits} credits</p>  <!-- credits NOT ESCAPED -->
    </div>
`).join('');
```

Also, `c.system_id` is used unescaped in the onclick attribute, enabling JS injection.

**Fix:** Escape ALL interpolated values, and use data attributes instead of inline onclick:
```javascript
container.innerHTML = courses.map(c => `
    <div class="..." data-action="stage-course"
         data-system-id="${escapeHtml(c.system_id)}"
         data-course-id="${escapeHtml(c.id)}"
         data-title="${escapeHtml(c.title)}"
         data-dept="${escapeHtml(c.department)}"
         data-credits="${escapeHtml(String(c.credits))}">
        <span class="...">${escapeHtml(c.system_id)}</span>
        ...
    </div>
`).join('');
```

---

### Bug #18: No File Size Validation in batch.js Upload

**File:** `django/app/plans/static/js/batch.js`
**Impact:** Large file uploads (100MB+) freeze the browser when read into memory with FileReader.

**Problem:**
```javascript
function handleFileUpload(file) {
    if (!file) return;
    const ext = file.name.toLowerCase();
    if (!ext.endsWith('.txt') && !ext.endsWith('.csv')) {
        showBatchToast('Please upload a .txt or .csv file', 'error');
        return;
    }
    const reader = new FileReader();  // NO SIZE CHECK
    reader.readAsText(file);
}
```

**Fix:**
```javascript
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

function handleFileUpload(file) {
    if (!file) return;
    if (file.size > MAX_FILE_SIZE) {
        showBatchToast('File too large (max 5MB)', 'error');
        return;
    }
    ...
}
```

---

### Bug #19: Batch Validation Doesn't Deduplicate Input

**File:** `django/app/plans/views/batch_views.py` lines 36-75
**Impact:** Same course identifier submitted twice gets validated twice, potentially adding duplicates.

**Problem:**
```python
for raw_input in identifiers:
    raw_input = raw_input.strip()
    if not raw_input:
        continue
    # No deduplication — same identifier processed multiple times
```

**Fix:**
```python
seen = set()
for raw_input in identifiers:
    raw_input = raw_input.strip()
    if not raw_input or raw_input.lower() in seen:
        continue
    seen.add(raw_input.lower())
    ...
```

---

### Bug #20: Missing RBAC on api_search_courses

**File:** `django/app/plans/views/plan_views.py` lines 96-102
**Impact:** Any user can enumerate the entire course catalog via the search API.

**Problem:**
```python
async def api_search_courses(request):  # NO @require_admin
    q = request.GET.get('q', '')
    ...
```

**Fix:**
```python
@require_admin
async def api_search_courses(request):
    ...
```

---

### Bug #21: Unvalidated GET Parameter Length in plan_list

**File:** `django/app/plans/views/plan_views.py` lines 62-64
**Impact:** Extremely long search queries passed to backend could cause memory/performance issues.

**Problem:**
```python
async def plan_list(request):
    search_query = request.GET.get('q', '')  # No length limit
    plans = await get_plans(search_query if search_query else None)
```

**Fix:**
```python
search_query = request.GET.get('q', '').strip()[:255]
```

---

### Bug #22: History Modal Fetch Missing CSRF Header

**File:** `django/app/plans/templates/plans/history_modal.html`
**Impact:** If Django's CSRF middleware is configured to check GET requests (non-default but possible), the audit log fetch would fail.

**Problem:**
```javascript
fetch('/api/audit-log/' + planId + '/')  // No headers
```

**Fix:**
```javascript
fetch(`/api/audit-log/${planId}/`, {
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
})
```

---

### Bug #23: Missing RBAC on api_get_course_list_detail

**File:** `django/app/plans/views/plan_views.py` lines 105-110
**Impact:** Any user can retrieve course list contents.

**Problem:**
```python
async def api_get_course_list_detail(request, list_id):  # NO @require_admin
    result = await get_course_list_detail(list_id)
    ...
```

**Fix:**
```python
@require_admin
async def api_get_course_list_detail(request, list_id):
    ...
```

---

### Bug #24: No Rate Limiting on Any Endpoint

**File:** All view files
**Impact:** No protection against brute force or DoS attacks on any endpoint.

**Fix (minimal):** Add Django middleware for basic rate limiting, or use `django-ratelimit`:
```python
# pip install django-ratelimit
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='60/m', method='ALL')
async def api_search_courses(request):
    ...
```

For production, handle at nginx level:
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
location /api/ {
    limit_req zone=api burst=10;
    ...
}
```

---

## LOW

### Bug #25: Hardcoded Color Values Instead of CSS Variables

**File:** Multiple template files
**Impact:** Theming or color changes require find-and-replace across dozens of files.

**Problem:** Colors like `#a51c30`, `#801b30`, `#fde6e6` appear in 50+ places across templates.

**Fix:** CSS variables are already defined in `layout.html` (lines 44-59) but not used in templates. Replace hardcoded values:
```html
<!-- Before -->
<button class="bg-[#a51c30] hover:bg-[#801b30] text-white">

<!-- After (using Tailwind's theme config already in layout.html) -->
<button class="bg-myh-700 hover:bg-myh-900 text-white">
```

---

### Bug #26: No Loading State / Double-Click Protection

**File:** `django/app/plans/static/js/plans.js` lines 16-63
**Impact:** Users can double-click Save buttons, triggering duplicate API calls and potential data corruption.

**Problem:**
```javascript
async function saveDraft(planId, reqId) {
    // No button disable during request
    const changes = getChanges(planId, reqId);
    try {
        await fetch(...);
        showToast('Draft saved');
    } catch (err) {
        showToast('Error saving draft', 'error');
    }
}
```

**Fix:**
```javascript
async function saveDraft(planId, reqId) {
    const btn = event?.target;
    if (btn) btn.disabled = true;
    try {
        const changes = getChanges(planId, reqId);
        await fetch(...);
        showToast('Draft saved');
    } catch (err) {
        showToast('Error saving draft', 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
}
```

---

### Bug #27: Error Messages Leak Internal Structure

**File:** `fastapi/app/routers/plans.py`, `courses.py`, `audit_log.py`
**Impact:** Messages like "Plan not found" or "Requirement not found" confirm entity names and API structure to attackers.

**Problem:**
```python
raise HTTPException(status_code=404, detail="Plan not found")
raise HTTPException(status_code=404, detail="Requirement not found")
```

**Fix:** Use generic messages in production:
```python
import os

def not_found_detail(entity: str = "Resource") -> str:
    if os.environ.get("DJANGO_DEBUG", "False").lower() == "true":
        return f"{entity} not found"
    return "Not found"

raise HTTPException(status_code=404, detail=not_found_detail("Plan"))
```

---

## Notes

- All line numbers reference the codebase as of 2026-02-14
- Bugs are numbered #1-#27 for cross-referencing in fix PRs
- The XSS bugs (#3, #4, #17) share a common fix pattern (data attributes) — fix them together
- The RBAC bugs (#1, #12, #20, #23) are all one-line decorator additions — batch fix
- Settings bugs (#6, #7, #8) should be fixed together with environment variable support
