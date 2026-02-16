# AAR Admin — Playwright E2E Test Specification v1

**Date:** 2026-02-14
**Purpose:** Complete test spec for another LLM to implement Playwright browser tests
**Test Count:** 55 test cases across 8 test files
**Framework:** pytest-playwright (Python)

---

## Table of Contents

1. [Setup Instructions](#1-setup-instructions)
2. [Test Organization](#2-test-organization)
3. [Shared Fixtures (conftest.py)](#3-shared-fixtures)
4. [Test Cases by File](#4-test-cases)
5. [AJAX Interception Patterns](#5-ajax-interception)
6. [Selectors Reference](#6-selectors-reference)
7. [Timing & Debounce Reference](#7-timing-reference)

---

## 1. Setup Instructions

### Prerequisites

Both servers must be running:
```bash
# Terminal 1 — FastAPI (port 9223)
cd aar_admin_django/fastapi/app
uv run uvicorn main:app --host 0.0.0.0 --port 9223 --reload

# Terminal 2 — Django (port 8000)
cd aar_admin_django/django/app
uv run python manage.py runserver 0.0.0.0:8000
```

### Install Dependencies

Add to `aar_admin_django/django/pyproject.toml` under `[project.optional-dependencies]`:
```toml
[project.optional-dependencies]
test = [
    "pytest>=8.0",
    "pytest-playwright>=0.5.0",
    "pytest-asyncio>=0.24",
]
```

Then install:
```bash
cd aar_admin_django/django
uv pip install -e ".[test]"
playwright install chromium
```

### Directory Structure

Create:
```
aar_admin_django/
└── tests/
    └── e2e/
        ├── conftest.py              # Shared fixtures
        ├── test_plan_list.py        # Plan list page (4 tests)
        ├── test_plan_detail.py      # Plan detail + requirements (6 tests)
        ├── test_modals.py           # All 5 modals (16 tests)
        ├── test_batch.py            # Batch add page (8 tests)
        ├── test_lookup.py           # Course lookup page (5 tests)
        ├── test_rbac.py             # Role switching + access control (7 tests)
        ├── test_pending_changes.py  # SessionStorage draft system (5 tests)
        └── test_csv_export.py       # CSV download (4 tests)
```

### Run Tests

```bash
cd aar_admin_django
pytest tests/e2e/ -v --headed    # With browser visible (debugging)
pytest tests/e2e/ -v             # Headless (CI)
pytest tests/e2e/ -v -k "rbac"   # Run specific test file
```

### pytest.ini / pyproject.toml Config

Add to `aar_admin_django/django/pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["../tests"]
asyncio_mode = "auto"
```

Or create `aar_admin_django/pytest.ini`:
```ini
[pytest]
testpaths = tests
asyncio_mode = auto
```

---

## 2. Test Organization

| File | Tests | Scope |
|------|-------|-------|
| `test_plan_list.py` | 4 | Page load, search, clear, click plan |
| `test_plan_detail.py` | 6 | Page load, back button, requirements, expand/collapse, empty state, header actions |
| `test_modals.py` | 16 | Add Course (5), Edit Validity (3), Requirement (3), Confirmation (2), History (3) |
| `test_batch.py` | 8 | Plan/req selection, file upload, text input, validate, resolve, add matches, template, catalog search |
| `test_lookup.py` | 5 | Search, select course, view usage, empty usage, restricted access |
| `test_rbac.py` | 7 | Switch roles, admin-only buttons, 403 enforcement, batch/lookup access |
| `test_pending_changes.py` | 5 | Add shows footer, remove shows strikethrough, save draft, discard, persistence |
| `test_csv_export.py` | 4 | Download triggers, content validation, filename, empty plan |

---

## 3. Shared Fixtures (conftest.py)

```python
"""
Shared fixtures for AAR Admin E2E tests.
All tests require both servers running: Django on :8000, FastAPI on :9223.
"""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8000"
FASTAPI_URL = "http://localhost:9223"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Set default browser context args."""
    return {
        **browser_context_args,
        "base_url": BASE_URL,
        "viewport": {"width": 1280, "height": 900},
    }


@pytest.fixture
def admin_page(page: Page) -> Page:
    """Page with ADMIN_USER role set via session cookie.

    Steps:
    1. Navigate to any page to establish session
    2. POST to /set-role/ with role=ADMIN_USER
    3. Reload to apply role
    """
    page.goto("/")
    # Get CSRF token from the page
    page.goto("/plans/conc_cs/")  # Plan detail has {% csrf_token %}
    csrf_token = page.locator("[name=csrfmiddlewaretoken]").input_value()

    # Set role via API
    response = page.request.post(
        f"{BASE_URL}/set-role/",
        form={"role": "ADMIN_USER"},
        headers={"X-CSRFToken": csrf_token, "Cookie": page.context.cookies()[0]["value"] if page.context.cookies() else ""},
    )
    assert response.status == 200

    # Reload to apply
    page.reload()
    return page


@pytest.fixture
def dept_page(page: Page) -> Page:
    """Page with DEPT_USER role set (default role)."""
    page.goto("/")
    return page


@pytest.fixture
def set_role(page: Page):
    """Helper fixture to switch roles mid-test.

    Usage: set_role("ADMIN_USER") or set_role("DEPT_USER")
    """
    def _set_role(role: str):
        # Navigate to plan detail to get CSRF token
        page.goto("/plans/conc_cs/")
        csrf_token = page.locator("[name=csrfmiddlewaretoken]").input_value()
        page.evaluate(f"""
            fetch('/set-role/', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': '{csrf_token}'
                }},
                body: 'role={role}'
            }})
        """)
        page.reload()
    return _set_role


# Known test data (from seed_data.py)
KNOWN_PLAN_ID = "conc_cs"           # Computer Science Concentration
KNOWN_PLAN_NAME = "Computer Science"
KNOWN_REQ_ID = "core_cs"            # Core CS requirement
KNOWN_REQ_TITLE = "Core Computer Science"
KNOWN_COURSE_ID = "CS50"            # Intro to CS
KNOWN_SYSTEM_ID = "SYS_001"         # System ID for CS50
KNOWN_COURSE_LIST_ID = "list_intro_cs"  # Intro CS course list


def wait_for_preline(page: Page):
    """Wait for Preline JS library to initialize."""
    page.wait_for_function("typeof HSOverlay !== 'undefined'")


def wait_for_toast(page: Page, text: str = None):
    """Wait for a toast notification to appear."""
    toast = page.locator("#toast-container > div").last
    expect(toast).to_be_visible(timeout=5000)
    if text:
        expect(toast).to_contain_text(text)
    return toast
```

**IMPORTANT for the implementing LLM:**
- The `KNOWN_*` constants above are placeholders. Read `aar_admin_django/fastapi/app/services/seed_data.py` to get the actual plan IDs, requirement IDs, course IDs, and system IDs from the seed data.
- The `admin_page` fixture uses the `/set-role/` endpoint which sets `request.session['user_role']`. This requires the Django session cookie to be present.
- Preline JS library initializes asynchronously — always call `wait_for_preline(page)` before interacting with modals, dropdowns, or tabs.

---

## 4. Test Cases

### 4.1 test_plan_list.py

```
File: tests/e2e/test_plan_list.py
Dependencies: conftest.py fixtures
Page: / (plan list)
```

#### Test 1: `test_plan_list_loads`
- **Preconditions:** None (default DEPT_USER)
- **Steps:**
  1. `page.goto("/")`
  2. Wait for page load
- **Assertions:**
  - Page title contains "AAR Admin"
  - At least one plan card is visible: `page.locator(".grid > a").count() > 0`
  - Header is visible with "AAR Admin" text
  - Tab navigation shows "Plans" as active: `expect(page.locator("[data-active-tab='plans']")).to_be_visible()`

#### Test 2: `test_plan_list_search`
- **Preconditions:** None
- **Steps:**
  1. `page.goto("/")`
  2. Fill search input: `page.locator("input[name='q']").fill("Computer")`
  3. Submit form (press Enter or click search button)
- **Assertions:**
  - URL contains `?q=Computer`
  - Results are filtered — plan cards visible contain "Computer" in text
  - Search input retains the query value

#### Test 3: `test_plan_list_clear_search`
- **Preconditions:** Start on `/?q=Computer`
- **Steps:**
  1. `page.goto("/?q=Computer")`
  2. Clear search input: `page.locator("input[name='q']").fill("")`
  3. Submit form
- **Assertions:**
  - URL is `/` (no query param)
  - All plans are shown (count matches full list)

#### Test 4: `test_plan_list_click_plan_navigates`
- **Preconditions:** None
- **Steps:**
  1. `page.goto("/")`
  2. Click first plan card: `page.locator(".grid > a").first.click()`
- **Assertions:**
  - URL matches `/plans/{plan_id}/` pattern
  - Plan detail page loads with plan name in heading

---

### 4.2 test_plan_detail.py

```
File: tests/e2e/test_plan_detail.py
Dependencies: admin_page fixture, KNOWN_PLAN_ID
Page: /plans/{plan_id}/
```

#### Test 5: `test_plan_detail_loads`
- **Preconditions:** ADMIN_USER role
- **Steps:**
  1. `admin_page.goto(f"/plans/{KNOWN_PLAN_ID}/")`
- **Assertions:**
  - Plan name heading visible: `expect(page.locator("h1")).to_contain_text(KNOWN_PLAN_NAME)`
  - Plan type badge visible
  - "Download Courselists" link visible
  - "View Audit Log" button visible
  - "Add New Requirement" button visible (admin only)
  - At least one requirement section: `page.locator("[data-req-section]").count() > 0`
  - CSRF token present: `page.locator("[name=csrfmiddlewaretoken]").count() == 1`

#### Test 6: `test_plan_detail_back_button`
- **Preconditions:** On plan detail page
- **Steps:**
  1. `page.goto(f"/plans/{KNOWN_PLAN_ID}/")`
  2. Click "Back to Plans" link
- **Assertions:**
  - URL is `/` (plan list)

#### Test 7: `test_requirement_section_expand_collapse`
- **Preconditions:** On plan detail page
- **Steps:**
  1. `page.goto(f"/plans/{KNOWN_PLAN_ID}/")`
  2. `wait_for_preline(page)`
  3. Get first requirement's collapse toggle: `page.locator("[data-hs-collapse]").first`
  4. Verify body is initially hidden (Preline default)
  5. Click toggle
  6. Wait for animation
- **Assertions:**
  - After click: requirement body (`#req-{reqId}`) is visible
  - Course rows are visible inside the body
  - Click again: body hides

#### Test 8: `test_requirement_shows_badges`
- **Preconditions:** Plan with requirements that have min courses/units/GPA
- **Steps:**
  1. `page.goto(f"/plans/{KNOWN_PLAN_ID}/")`
- **Assertions:**
  - Badge "Min. Courses:" visible on requirements that have it
  - Badge "Min. Units:" visible where applicable
  - Badge "Min. GPA:" visible where applicable

#### Test 9: `test_plan_detail_no_requirements_empty_state`
- **Preconditions:** Need a plan with zero requirements (may need to create test data or use a known empty plan)
- **Steps:**
  1. Navigate to empty plan
- **Assertions:**
  - "No requirements defined for this plan yet." message visible

#### Test 10: `test_course_row_displays_info`
- **Preconditions:** Expanded requirement with courses
- **Steps:**
  1. `page.goto(f"/plans/{KNOWN_PLAN_ID}/")`
  2. Expand first requirement
- **Assertions:**
  - Course row shows: system ID badge (monospace), course ID, course title
  - Wildcard courses show "wildcard" badge
  - Admin buttons visible: Edit Validity, Exclude/Include, Remove

---

### 4.3 test_modals.py

```
File: tests/e2e/test_modals.py
Dependencies: admin_page fixture, wait_for_preline
Page: /plans/{plan_id}/
```

#### Add Course Modal (5 tests)

#### Test 11: `test_add_course_modal_opens`
- **Preconditions:** ADMIN_USER, on plan detail
- **Steps:**
  1. `admin_page.goto(f"/plans/{KNOWN_PLAN_ID}/")`
  2. `wait_for_preline(page)`
  3. Click "Add Courses" button on first requirement
- **Assertions:**
  - Modal `#add-course-modal` becomes visible (check for class `open` or lack of `hidden`)
  - Modal title shows requirement name
  - Search tab is active by default
  - Search input is empty

#### Test 12: `test_add_course_modal_search`
- **Preconditions:** Add Course modal is open
- **Steps:**
  1. Open modal (from test 11 steps)
  2. Type "CS" in search input `#acm-search-input`
  3. Wait 400ms (300ms debounce + buffer)
- **Assertions:**
  - Intercept or wait for response: `page.expect_response("**/api/courses/search/?q=CS")`
  - Search results appear in `#acm-search-results`
  - Results contain course items with system ID badges

#### Test 13: `test_add_course_modal_stage_and_add`
- **Preconditions:** Search results visible in modal
- **Steps:**
  1. Open modal, search for "CS"
  2. Click on a search result to stage it
  3. Verify staged area appears (`#acm-staging-container` becomes visible)
  4. Click "Add Selected Courses" button `#acm-add-staged-btn`
- **Assertions:**
  - After staging: `#acm-staging-container` visible, course tag shown in `#acm-staged`
  - After add: modal closes, toast "Added 1 course(s)" appears
  - Changes footer appears on the requirement section

#### Test 14: `test_add_course_modal_wildcards`
- **Preconditions:** Add Course modal open, Wildcards tab
- **Steps:**
  1. Open modal
  2. Click "Wildcards" tab: `page.locator("[data-hs-tab='#acm-tabpane-wildcards']").click()`
  3. Enter patterns in textarea `#acm-wildcard-input`: `"CS 1*\nMATH 2#"`
  4. Click "Review Patterns" button `#acm-review-wildcards-btn`
  5. Verify review section shows valid count
  6. Click "Add Wildcards" button `#acm-add-wildcards-btn`
- **Assertions:**
  - After review: `#acm-wildcard-review` visible, valid count shows "2"
  - After add: modal closes, toast "Added 2 wildcard(s)" appears

#### Test 15: `test_add_course_modal_from_list`
- **Preconditions:** Add Course modal open, "Add From List" tab
- **Steps:**
  1. Open modal
  2. Click "Add From List" tab: `page.locator("[data-hs-tab='#acm-tabpane-from-list']").click()`
  3. Select a course list from dropdown `#acm-course-list-select`
  4. Wait for response: `page.expect_response("**/api/course-lists/**")`
  5. Verify preview shows courses
  6. Click "Add All from List" button `#acm-add-from-list-btn`
- **Assertions:**
  - After select: `#acm-list-preview` shows course entries
  - After add: modal closes, toast "Added X course(s) from list" appears

#### Edit Validity Modal (3 tests)

#### Test 16: `test_edit_validity_modal_opens`
- **Preconditions:** ADMIN_USER, requirement expanded, course rows visible
- **Steps:**
  1. Navigate to plan, expand requirement
  2. Click "Edit validity" button (calendar icon) on a course row
- **Assertions:**
  - Modal `#edit-validity-modal` opens
  - Course identifier displayed in `#evm-course-id`
  - "ALWAYS" radio is checked by default

#### Test 17: `test_edit_validity_change_to_terms`
- **Preconditions:** Edit Validity modal open
- **Steps:**
  1. Open modal on a course
  2. Click "TERMS" radio button
  3. Verify terms checkboxes appear
  4. Check "Fall 2025" and "Spring 2024"
  5. Click "Save Validity" button `#evm-save-btn`
- **Assertions:**
  - After radio change: `#evm-terms-container` becomes visible
  - After save: modal closes, toast "Validity updated" appears
  - Changes footer appears on the requirement

#### Test 18: `test_edit_validity_date_range`
- **Preconditions:** Edit Validity modal open
- **Steps:**
  1. Open modal
  2. Click "DATE_RANGE" radio
  3. Fill `#evm-date-from` and `#evm-date-to`
  4. Save
- **Assertions:**
  - `#evm-date-container` visible after radio change
  - Modal closes, toast appears after save

#### Requirement Modal (3 tests)

#### Test 19: `test_add_requirement_modal`
- **Preconditions:** ADMIN_USER on plan detail
- **Steps:**
  1. Click "Add New Requirement" button in header
  2. Modal `#requirement-modal` opens
  3. Fill title `#rm-req-title`: "Test Requirement"
  4. Fill description, courses count, units
  5. Click "Save Requirement" `#rm-save-btn`
- **Assertions:**
  - Modal title says "Add Requirement"
  - Intercept POST to `/plans/{planId}/requirements/add/`
  - Response is 200
  - Toast "Requirement added" appears
  - Page reloads (check for new requirement in DOM)

#### Test 20: `test_edit_requirement_modal`
- **Preconditions:** ADMIN_USER, requirement exists
- **Steps:**
  1. Click edit (pencil) icon on a requirement header
  2. Modal opens with pre-filled values
  3. Change title to "Updated Title"
  4. Save
- **Assertions:**
  - Modal title says "Edit Requirement"
  - Fields are pre-populated
  - POST to `/plans/{planId}/requirements/{reqId}/edit/` succeeds
  - Toast "Requirement updated" appears

#### Test 21: `test_requirement_modal_title_required`
- **Preconditions:** Requirement modal open
- **Steps:**
  1. Open add requirement modal
  2. Leave title empty
  3. Click Save
- **Assertions:**
  - Toast "Title is required" (error) appears
  - Modal stays open

#### Confirmation Modal (2 tests)

#### Test 22: `test_confirmation_modal_shows_counts`
- **Preconditions:** Changes exist (courses added/removed)
- **Steps:**
  1. Stage changes (add a course, remove a course)
  2. Click "Save Changes" on requirement footer
  3. Confirmation modal `#confirmation-modal` opens
- **Assertions:**
  - Add count `#cm-add-count` shows correct number
  - Remove count `#cm-remove-count` shows correct number
  - "Confirm & Save" button `#cm-confirm-btn` is disabled until scope selected

#### Test 23: `test_confirmation_modal_select_scope_and_confirm`
- **Preconditions:** Confirmation modal open
- **Steps:**
  1. From test 22
  2. Select "All Students" radio
  3. Click "Confirm & Save"
- **Assertions:**
  - Button becomes enabled after scope selection
  - POST to `/plans/{planId}/requirements/{reqId}/save-changes/` fires
  - Toast "Changes saved" appears
  - Page reloads

#### History Modal (3 tests)

#### Test 24: `test_history_modal_opens_and_loads`
- **Preconditions:** Plan with audit log entries
- **Steps:**
  1. `page.goto(f"/plans/{KNOWN_PLAN_ID}/")`
  2. Click "View Audit Log" button
  3. Wait for modal `#history-modal` to open
- **Assertions:**
  - Loading spinner `#history-modal-loading` appears briefly
  - Intercept GET `/api/audit-log/{planId}/`
  - Entries appear in `#history-modal-entries` with timeline layout
  - Each entry shows: timestamp, role badge, action text

#### Test 25: `test_history_modal_empty_state`
- **Preconditions:** Plan with no audit entries (or mock empty response)
- **Steps:**
  1. Navigate to plan with no history
  2. Open history modal
- **Assertions:**
  - Empty state `#history-modal-empty` visible: "No audit log entries"

#### Test 26: `test_history_modal_timestamp_formatting`
- **Preconditions:** History modal with entries
- **Steps:**
  1. Open history modal with entries
  2. Check timestamp text
- **Assertions:**
  - Recent entries show relative time ("Just now", "X minutes ago")
  - Older entries show formatted date

---

### 4.4 test_batch.py

```
File: tests/e2e/test_batch.py
Dependencies: admin_page fixture
Page: /batch/
```

#### Test 27: `test_batch_page_loads`
- **Preconditions:** ADMIN_USER
- **Steps:**
  1. `admin_page.goto("/batch/")`
- **Assertions:**
  - Plan dropdown `#batch-plan-select` visible with options
  - Requirement dropdown `#batch-req-select` visible but disabled
  - Import mode radios visible
  - Input panel visible

#### Test 28: `test_batch_plan_req_selection`
- **Preconditions:** On batch page
- **Steps:**
  1. Select a plan from `#batch-plan-select`
  2. Wait for requirements to load: `page.expect_response("**/api/batch/plan/*/requirements/")`
  3. Select a requirement from `#batch-req-select`
- **Assertions:**
  - After plan select: req dropdown becomes enabled and populated
  - After req select: input area is ready

#### Test 29: `test_batch_text_input_validate`
- **Preconditions:** Plan and requirement selected
- **Steps:**
  1. Select plan and req
  2. Enter identifiers in textarea `#batch-text-input`: `"CS50\nMATH101\nINVALID999"`
  3. Click "Validate Input" `#batch-validate-btn`
- **Assertions:**
  - Intercept POST to `/batch/api/batch/validate/`
  - Results panel appears
  - Stats show: Total: 3, some matches, some no-match
  - Results table has rows for each input

#### Test 30: `test_batch_file_upload`
- **Preconditions:** Plan and req selected
- **Steps:**
  1. Create a test CSV file with known course IDs
  2. Upload via file input (use `page.set_input_files()` on the hidden file input)
- **Assertions:**
  - Textarea `#batch-text-input` gets populated with file contents
  - File extension validated (.csv or .txt)

#### Test 31: `test_batch_resolve_multiple_matches`
- **Preconditions:** Validation results with MULTIPLE_MATCHES status
- **Steps:**
  1. Validate an identifier that has multiple candidates
  2. Click "Resolve" button on the MULTIPLE_MATCHES row
  3. Resolution modal appears with candidate checkboxes
  4. Check one candidate
  5. Click "Confirm Selection"
- **Assertions:**
  - Resolution modal shows candidate options
  - After confirm: row status changes to "Resolved"
  - "Add Valid Matches" button updates count

#### Test 32: `test_batch_add_valid_matches`
- **Preconditions:** Validated results with some EXACT_MATCH entries
- **Steps:**
  1. After validation, click "Add X Valid Matches" button `#batch-add-valid`
- **Assertions:**
  - Intercept POST to `/plans/{planId}/requirements/{reqId}/save-changes/`
  - Toast shows success message
  - UI resets

#### Test 33: `test_batch_download_template`
- **Preconditions:** On batch page
- **Steps:**
  1. Click "Download Template" `#batch-download-template`
- **Assertions:**
  - Download triggers (check `page.expect_download()`)
  - File has correct name: `batch_template_catalog.csv` or `.txt`

#### Test 34: `test_batch_catalog_search`
- **Preconditions:** On batch page, "Catalog Search" tab
- **Steps:**
  1. Click catalog search tab
  2. Type "CS" in search input `#batch-catalog-search`
  3. Wait 400ms (300ms debounce + buffer)
  4. Click a result to stage it
- **Assertions:**
  - Search results appear (client-side filter of `window.allCourses`)
  - Staged courses section shows the selected course

---

### 4.5 test_lookup.py

```
File: tests/e2e/test_lookup.py
Dependencies: admin_page, dept_page fixtures
Page: /lookup/
```

#### Test 35: `test_lookup_page_loads_admin`
- **Preconditions:** ADMIN_USER
- **Steps:**
  1. `admin_page.goto("/lookup/")`
- **Assertions:**
  - Search input `#course-search` visible
  - No restricted access message

#### Test 36: `test_lookup_search_courses`
- **Preconditions:** ADMIN_USER on lookup page
- **Steps:**
  1. Type "CS" in `#course-search`
  2. Wait 300ms (200ms debounce + buffer)
- **Assertions:**
  - Dropdown results `#search-results` appears
  - Results contain courses matching "CS"

#### Test 37: `test_lookup_select_course_shows_usage`
- **Preconditions:** Search results visible
- **Steps:**
  1. Search and get results
  2. Click on a course result
- **Assertions:**
  - Selected course panel `#selected-course-panel` appears with course details
  - Usage results panel `#usage-results-panel` appears
  - Loading spinner shows briefly, then usage data loads
  - Intercept GET `/lookup/api/courses/{systemId}/usage/`
  - Usage grouped by plan name

#### Test 38: `test_lookup_empty_usage`
- **Preconditions:** Select a course with no usage
- **Steps:**
  1. Search for a course not used in any plan
  2. Click to select it
- **Assertions:**
  - Empty state `#usage-empty` shows: "This course is not used in any plans"

#### Test 39: `test_lookup_restricted_for_dept_user`
- **Preconditions:** DEPT_USER role
- **Steps:**
  1. `dept_page.goto("/lookup/")`
- **Assertions:**
  - Returns 403 JSON response OR shows restricted access message
  - Search input is NOT visible

---

### 4.6 test_rbac.py

```
File: tests/e2e/test_rbac.py
Dependencies: set_role fixture
Page: Various
```

#### Test 40: `test_role_switch_to_admin`
- **Preconditions:** Default DEPT_USER
- **Steps:**
  1. `page.goto("/")`
  2. Call `set_role("ADMIN_USER")`
  3. Navigate to plan detail
- **Assertions:**
  - "Add New Requirement" button visible
  - Course row action buttons (Edit Validity, Exclude, Remove) visible
  - "Add Courses" button visible on requirement sections

#### Test 41: `test_role_switch_to_dept`
- **Preconditions:** Currently ADMIN_USER
- **Steps:**
  1. `set_role("ADMIN_USER")`
  2. Navigate to plan detail
  3. `set_role("DEPT_USER")`
  4. Navigate to same plan detail
- **Assertions:**
  - "Add New Requirement" button NOT visible
  - Course row action buttons NOT visible
  - "Add Courses" button NOT visible

#### Test 42: `test_admin_only_buttons_hidden_for_dept`
- **Preconditions:** DEPT_USER
- **Steps:**
  1. `page.goto(f"/plans/{KNOWN_PLAN_ID}/")`
- **Assertions:**
  - Count of `button:has-text("Add New Requirement")` is 0
  - Count of `button:has-text("Add Courses")` is 0
  - Count of `button:has-text("Exclude")` is 0
  - Count of `button:has-text("Remove")` (trash icon buttons) is 0

#### Test 43: `test_403_on_protected_post_endpoints`
- **Preconditions:** DEPT_USER
- **Steps:**
  1. Attempt POST to `/plans/{KNOWN_PLAN_ID}/requirements/add/` via `page.request.post()`
  2. Attempt POST to `/plans/{KNOWN_PLAN_ID}/requirements/{KNOWN_REQ_ID}/save-changes/`
- **Assertions:**
  - Both return HTTP 403
  - Response body contains `"Admin access required"`

#### Test 44: `test_batch_page_requires_admin`
- **Preconditions:** DEPT_USER
- **Steps:**
  1. `page.goto("/batch/")`
- **Assertions:**
  - Returns 403 or redirects
  - Batch add form is NOT visible

#### Test 45: `test_lookup_page_requires_admin`
- **Preconditions:** DEPT_USER
- **Steps:**
  1. `page.goto("/lookup/")`
- **Assertions:**
  - Returns 403 or shows restricted message
  - Search input NOT visible

#### Test 46: `test_role_persists_across_navigation`
- **Preconditions:** Set ADMIN_USER
- **Steps:**
  1. `set_role("ADMIN_USER")`
  2. Navigate to plan list
  3. Click a plan
  4. Navigate back
  5. Navigate to batch
- **Assertions:**
  - Admin features visible on all pages
  - No re-authentication needed

---

### 4.7 test_pending_changes.py

```
File: tests/e2e/test_pending_changes.py
Dependencies: admin_page fixture
Page: /plans/{plan_id}/
```

#### Test 47: `test_add_course_shows_changes_footer`
- **Preconditions:** ADMIN_USER, on plan detail, requirement expanded
- **Steps:**
  1. Open Add Course modal on a requirement
  2. Search, stage, and add a course
  3. Modal closes
- **Assertions:**
  - Changes footer `[data-changes-footer]` on that requirement becomes visible
  - Footer shows "You have unsaved changes"
  - Three buttons visible: "Cancel", "Save Draft", "Save Changes"

#### Test 48: `test_remove_course_shows_strikethrough`
- **Preconditions:** ADMIN_USER, requirement with courses
- **Steps:**
  1. Expand requirement
  2. Click "Remove" (trash) button on a course row
- **Assertions:**
  - Course row gets classes: `bg-red-50`, `opacity-60`, `line-through`
  - Changes footer appears

#### Test 49: `test_save_draft_persists`
- **Preconditions:** Pending changes exist
- **Steps:**
  1. Make changes (add or remove a course)
  2. Click "Save Draft" button
  3. Wait for response
- **Assertions:**
  - Intercept POST to `/plans/{planId}/requirements/{reqId}/save-draft/`
  - Toast "Draft saved" appears

#### Test 50: `test_discard_draft_clears_changes`
- **Preconditions:** Pending changes exist
- **Steps:**
  1. Make changes
  2. Click "Cancel" button
- **Assertions:**
  - Page reloads
  - Changes footer is hidden after reload
  - Course rows return to normal (no strikethrough, no green highlight)

#### Test 51: `test_changes_persist_in_session_storage`
- **Preconditions:** Changes made but not saved
- **Steps:**
  1. Add a course to a requirement
  2. Navigate away (click "Back to Plans")
  3. Navigate back to the same plan detail
- **Assertions:**
  - Changes footer is still visible (sessionStorage preserved)
  - Added course still highlighted
  - Use `page.evaluate("sessionStorage.getItem('draft_...')")` to verify data

---

### 4.8 test_csv_export.py

```
File: tests/e2e/test_csv_export.py
Dependencies: admin_page fixture
Page: /plans/{plan_id}/
```

#### Test 52: `test_csv_download_triggers`
- **Preconditions:** On plan detail
- **Steps:**
  1. `page.goto(f"/plans/{KNOWN_PLAN_ID}/")`
  2. Click "Download Courselists" link
  3. Wait for download: `with page.expect_download() as download_info:`
- **Assertions:**
  - Download triggers
  - Filename ends with `_Requirements.csv`
  - Download completes without error

#### Test 53: `test_csv_content_has_headers`
- **Preconditions:** Downloaded CSV file
- **Steps:**
  1. Download CSV (from test 52)
  2. Read file content
- **Assertions:**
  - First line: `Plan Name,Plan Type,Requirement Title,Description,Subject/Catalog,Course ID,Course Title,Department,Credits`
  - At least one data row after header
  - Data rows contain plan name

#### Test 54: `test_csv_handles_wildcards`
- **Preconditions:** Plan with wildcard courses
- **Steps:**
  1. Download CSV from plan with wildcards
  2. Read content
- **Assertions:**
  - Wildcard rows have "WILDCARD" in the Course Title column

#### Test 55: `test_csv_export_404_for_invalid_plan`
- **Preconditions:** None
- **Steps:**
  1. `page.request.get(f"{BASE_URL}/plans/nonexistent_plan/export/")`
- **Assertions:**
  - Returns HTTP 404

---

## 5. AJAX Interception Patterns

### Intercept and verify real requests:

```python
def test_example_with_response_check(admin_page):
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")

    # Wait for a specific API call
    with page.expect_response("**/api/courses/search/?q=*") as response_info:
        page.locator("#acm-search-input").fill("CS")
        page.wait_for_timeout(400)  # debounce

    response = response_info.value
    assert response.status == 200
    data = response.json()
    assert "courses" in data
```

### Mock FastAPI responses (if needed):

```python
def test_with_mocked_api(page):
    # Mock the course search to return controlled data
    def handle_route(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body='{"courses": [{"system_id": "SYS_TEST", "id": "TEST101", "title": "Test Course", "department": "Testing", "credits": 4}]}'
        )

    page.route("**/api/courses/search/**", handle_route)
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    # ... interact with modal
```

### CSRF token handling in direct requests:

```python
def get_csrf_and_cookies(page):
    """Extract CSRF token and cookies for direct API calls."""
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    csrf = page.locator("[name=csrfmiddlewaretoken]").input_value()
    cookies = {c["name"]: c["value"] for c in page.context.cookies()}
    return csrf, cookies
```

---

## 6. Selectors Reference

### Element IDs

| ID | Element | Page |
|----|---------|------|
| `#requirements-container` | Main requirements wrapper | Plan Detail |
| `#add-course-modal` | Add Course modal overlay | Plan Detail |
| `#edit-validity-modal` | Edit Validity modal overlay | Plan Detail |
| `#requirement-modal` | Add/Edit Requirement modal | Plan Detail |
| `#confirmation-modal` | Confirm changes modal | Plan Detail |
| `#history-modal` | Audit log modal | Plan Detail |
| `#toast-container` | Toast notification container | All pages |
| `#acm-search-input` | Course search input (Add modal) | Plan Detail |
| `#acm-search-results` | Search results container | Plan Detail |
| `#acm-staging-container` | Staged courses container | Plan Detail |
| `#acm-staged` | Staged courses display | Plan Detail |
| `#acm-add-staged-btn` | "Add Selected" button | Plan Detail |
| `#acm-wildcard-input` | Wildcard patterns textarea | Plan Detail |
| `#acm-wildcard-review` | Wildcard review section | Plan Detail |
| `#acm-review-wildcards-btn` | "Review Patterns" button | Plan Detail |
| `#acm-add-wildcards-btn` | "Add Wildcards" button | Plan Detail |
| `#acm-course-list-select` | Course list dropdown | Plan Detail |
| `#acm-list-preview` | Course list preview | Plan Detail |
| `#acm-add-from-list-btn` | "Add All from List" button | Plan Detail |
| `#evm-plan-id` | Hidden plan ID (validity modal) | Plan Detail |
| `#evm-req-id` | Hidden req ID (validity modal) | Plan Detail |
| `#evm-identifier` | Hidden identifier (validity modal) | Plan Detail |
| `#evm-terms-container` | Terms checkbox container | Plan Detail |
| `#evm-date-container` | Date range container | Plan Detail |
| `#evm-save-btn` | "Save Validity" button | Plan Detail |
| `#rm-plan-id` | Hidden plan ID (requirement modal) | Plan Detail |
| `#rm-req-id` | Hidden req ID (requirement modal) | Plan Detail |
| `#rm-req-title` | Title input (requirement modal) | Plan Detail |
| `#rm-req-description` | Description textarea | Plan Detail |
| `#rm-save-btn` | "Save Requirement" button | Plan Detail |
| `#cm-add-count` | Additions count display | Plan Detail |
| `#cm-remove-count` | Removals count display | Plan Detail |
| `#cm-modify-count` | Modifications count display | Plan Detail |
| `#cm-confirm-btn` | "Confirm & Save" button | Plan Detail |
| `#history-modal-loading` | Loading spinner | Plan Detail |
| `#history-modal-empty` | Empty state message | Plan Detail |
| `#history-modal-entries` | Entries container | Plan Detail |
| `#batch-plan-select` | Plan dropdown | Batch Add |
| `#batch-req-select` | Requirement dropdown | Batch Add |
| `#batch-text-input` | Bulk text input textarea | Batch Add |
| `#batch-validate-btn` | "Validate Input" button | Batch Add |
| `#batch-add-valid` | "Add Valid Matches" button | Batch Add |
| `#batch-reset` | "Reset" button | Batch Add |
| `#batch-download-template` | Template download button | Batch Add |
| `#batch-catalog-search` | Catalog search input | Batch Add |
| `#batch-search-results` | Catalog search results | Batch Add |
| `#batch-staged-courses` | Staged courses container | Batch Add |
| `#course-search` | Course search input | Lookup |
| `#search-results` | Search results dropdown | Lookup |
| `#selected-course-panel` | Selected course info panel | Lookup |
| `#usage-results-panel` | Usage results panel | Lookup |
| `#usage-loading` | Loading spinner | Lookup |
| `#usage-results` | Usage data container | Lookup |
| `#usage-empty` | No usage message | Lookup |

### Data Attributes

| Attribute | Usage | Selector Example |
|-----------|-------|-----------------|
| `data-plan-id` | Plan ID on requirements container | `[data-plan-id]` |
| `data-req-section` | Requirement section ID | `[data-req-section="core_cs"]` |
| `data-identifier` | Course identifier on row | `[data-identifier="SYS_001"]` |
| `data-changes-footer` | Changes footer key | `[data-changes-footer="plan1\|req1"]` |
| `data-hs-collapse` | Preline collapse trigger | `[data-hs-collapse="#req-core_cs"]` |
| `data-hs-tab` | Preline tab trigger | `[data-hs-tab="#acm-tabpane-search"]` |
| `data-active-tab` | Active tab indicator | `[data-active-tab="plans"]` |

### Preline State Classes

| Class | Meaning |
|-------|---------|
| `open` | Modal/overlay is open |
| `hidden` | Element is hidden |
| `hs-collapse-open` | Collapse section is expanded |
| `hs-tab-active` | Tab is currently active |

### Visual State Classes (Pending Changes)

| Class | Meaning |
|-------|---------|
| `bg-red-50` | Course marked for removal |
| `opacity-60` | Course marked for removal (faded) |
| `line-through` | Course marked for removal (strikethrough) |
| `bg-green-50` | Course newly added |
| `bg-amber-50` | Course excluded |

---

## 7. Timing Reference

| Action | Debounce/Delay | Buffer for Tests |
|--------|---------------|-----------------|
| Course search (Add Course modal) | 300ms | Wait 400ms |
| Course search (Batch catalog) | 300ms | Wait 400ms |
| Course search (Lookup page) | 200ms | Wait 300ms |
| Search results blur (hide) | 200ms | Wait 300ms |
| Page reload after requirement save | 500ms | Wait 700ms |
| Toast auto-remove | 3000ms | Wait 3200ms |
| Toast fade-out animation | 300ms | — |
| Preline modal open animation | ~200ms | Wait 300ms |
| Preline collapse animation | ~200ms | Wait 300ms |

**General rule:** Add 100-200ms buffer to all debounce times in tests to account for JS execution overhead.

---

## Notes for the Implementing LLM

1. **Read seed data first:** Before writing any test, read `aar_admin_django/fastapi/app/services/seed_data.py` to get actual plan IDs, requirement IDs, course IDs, system IDs, and course list IDs. Replace all `KNOWN_*` constants in conftest.py.

2. **Preline initialization:** Preline JS library initializes on page load. If a test navigates to a new page and immediately tries to interact with modals/tabs, it may fail. Always call `wait_for_preline(page)` after navigation.

3. **CSRF handling:** Django CSRF middleware requires the `csrfmiddlewaretoken` hidden input on POST requests. The plan detail page has `{% csrf_token %}` but other pages may not. For direct API calls in tests, extract the token from plan detail first.

4. **Session cookies:** The `set_role` fixture uses signed cookies (SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'). The session is stored entirely in the cookie, not in a DB.

5. **Headless vs headed:** Some Preline animations may behave differently headless. Use `page.wait_for_timeout(300)` after modal open/close to ensure animations complete.

6. **Test isolation:** Each test should be independent. Don't rely on state from previous tests. Use fixtures to set up state.

7. **Known issues in the codebase:** See `tasks/bugs_v1.md` for 27 known bugs. Some tests may fail due to these bugs (especially XSS tests, RBAC bypass tests). Document expected failures.
