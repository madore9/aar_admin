# AAR Admin - Missing Features Specification

## Overview

This document details the features missing from the Django/FastAPI implementation compared to the original Google AI Studio version, along with test specifications for each.

---

## Feature 1: Course Lists Management

### 1.1 API Specification (FastAPI)

#### Endpoints to Create

**GET /aar/course-lists/**
- Returns all course lists
- Response: `{ "course_lists": [{ "id", "name", "description", "courses": [...] }] }`

**POST /aar/course-lists/**
- Create new course list
- Body: `{ "name": "string", "description": "string" }`
- Returns: 201 with created course list

**GET /aar/course-lists/{list_id}**
- Get single course list with all courses
- Response: `{ "id", "name", "description", "courses": [{ "identifier", "is_wildcard" }] }`

**PUT /aar/course-lists/{list_id}**
- Update course list metadata
- Body: `{ "name": "string", "description": "string" }`

**DELETE /aar/course-lists/{list_id}**
- Delete course list
- Returns: 204

**POST /aar/course-lists/{list_id}/courses**
- Add courses to list
- Body: `{ "courses": [{ "identifier": "string", "is_wildcard": boolean }] }`

**DELETE /aar/course-lists/{list_id}/courses/{identifier}**
- Remove single course from list
- Returns: 204

**POST /aar/course-lists/{list_id}/courses/bulk**
- Bulk add/remove courses
- Body: `{ "add": [...], "remove": [...] }`

### 1.2 Django Views

**GET /course-lists/**
- Display all course lists
- Requires: ADMIN_USER

**GET /course-lists/{list_id}/**
- View/edit single course list
- Shows usage in plans

### 1.3 Templates Needed

- `course_lists/course_lists.html` - Main page listing all lists
- `course_lists/course_list_detail.html` - Single list view
- `course_lists/add_course_list_modal.html` - Create new list
- `course_lists/edit_course_list_modal.html` - Edit list details
- `course_lists/add_courses_to_list_modal.html` - Add courses to list

### 1.4 Playwright Tests

```python
# tests/e2e/test_course_lists.py

def test_course_lists_page_loads(admin_page):
    """Test course lists page loads with admin."""
    page = admin_page
    page.goto("/course-lists/")
    expect(page.locator("h1")).to_contain_text("Course Lists")

def test_create_course_list(admin_page):
    """Test creating a new course list."""
    page = admin_page
    page.goto("/course-lists/")
    # Click "Create New List" button
    page.locator("button:has-text('Create New List')").click()
    # Fill form
    page.locator("#cl-name-input").fill("Test List")
    page.locator("#cl-description-input").fill("Test Description")
    page.locator("#cl-save-btn").click()
    # Verify success
    expect(page.locator("#toast-container")).to_contain_text("created")

def test_add_courses_to_list(admin_page):
    """Test adding courses to a course list."""
    page = admin_page
    page.goto("/course-lists/")
    # Click on a course list
    page.locator(".course-list-card").first.click()
    # Click "Add Courses" button
    page.locator("button:has-text('Add Courses')").click()
    # Search and add courses
    page.locator("#cl-search-input").fill("CS50")
    page.wait_for_timeout(500)
    page.locator("#cl-search-results > div").first.click()
    page.locator("#cl-add-selected-btn").click()
    # Verify added
    expect(page.locator(".course-item")).to_contain_text("CS50")

def test_edit_course_list_metadata(admin_page):
    """Test editing course list name/description."""
    page = admin_page
    page.goto("/course-lists/")
    # Click edit button on list
    page.locator("[data-action='edit-list']").first.click()
    page.locator("#cl-name-input").fill("Updated Name")
    page.locator("#cl-save-btn").click()
    expect(page.locator(".course-list-card")).to_contain_text("Updated Name")

def test_delete_course_list(admin_page):
    """Test deleting a course list."""
    page = admin_page
    page.goto("/course-lists/")
    # Click delete button
    page.locator("[data-action='delete-list']").first.click()
    # Confirm in modal
    page.locator("#cl-confirm-delete-btn").click()
    # Verify deleted
    expect(page.locator("#toast-container")).to_contain_text("deleted")

def test_course_list_usage_display(admin_page):
    """Test that usage in plans is displayed."""
    page = admin_page
    page.goto("/course-lists/")
    # Click on a list that is used in plans
    page.locator(".course-list-card").first.click()
    # Check for usage section
    usage_section = page.locator("#cl-usage-section")
    # Should show plans using this list

def test_course_list_restricted_for_dept(dept_page):
    """Test course lists page is admin only."""
    page = dept_page
    page.goto("/course-lists/")
    # Should be redirected or show 403
    expect(page.locator("h1")).not_to_contain_text("Course Lists")
```

---

## Feature 2: Shared List Updates

### 2.1 API Specification

**GET /aar/course-lists/{list_id}/usage**
- Get all plans/requirements using this course list
- Response: `{ "usage": [{ "plan_id", "plan_name", "req_id", "req_title" }] }`

**POST /aar/course-lists/{list_id}/sync**
- Sync changes to all plans using this list
- Body: `{ "changes": { "add": [...], "remove": [...] }, "scope": "all|incoming" }`
- Returns: 200 with audit log entries

### 2.2 Django Views

**GET /course-lists/{list_id}/sync/**
- Show sync confirmation modal with all affected plans

### 2.3 Template

- `course_lists/sync_confirmation_modal.html` - Confirm sync to all plans

### 2.4 Playwright Tests

```python
# tests/e2e/test_shared_updates.py

def test_sync_changes_to_all_plans(admin_page):
    """Test syncing changes to all plans using a course list."""
    page = admin_page
    page.goto("/course-lists/")
    # Click on a list
    page.locator(".course-list-card").first.click()
    # Make changes (add/remove courses)
    page.locator("button:has-text('Add Courses')").click()
    # ... add courses ...
    page.locator("#cl-save-changes-btn").click()
    # Click "Sync to Plans" button
    page.locator("button:has-text('Sync to Plans')").click()
    # Verify modal shows affected plans
    expect(page.locator("#sync-modal")).to_be_visible()
    expect(page.locator("#sync-affected-plans")).to_be_visible()
    # Select scope and confirm
    page.locator("input[value='all']").check()
    page.locator("#sync-confirm-btn").click()
    # Verify success
    expect(page.locator("#toast-container")).to_contain_text("synced")

def test_sync_scope_incoming_only(admin_page):
    """Test syncing only to incoming students."""
    page = admin_page
    page.goto("/course-lists/")
    # Navigate to list and make changes
    # Select "Incoming Students" scope
    page.locator("input[value='incoming']").check()
    page.locator("#sync-confirm-btn").click()
    # Verify only incoming affected
```

---

## Feature 3: Course Search Filtering

### 3.1 API Changes

**GET /aar/courses/search/**
- Add `field` query parameter
- Values: `all`, `id`, `title`, `department`
- Example: `/aar/courses/search/?q=CS&field=title`

### 3.2 Django Changes

- Add dropdown to search UI with field options
- Pass selected field to API

### 3.3 Playwright Tests

```python
# tests/e2e/test_search_filtering.py

def test_search_by_course_id(admin_page):
    """Test searching by course ID."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    # Open Add Course modal
    page.locator("button:has-text('Add Courses')").first.click()
    # Select "Course ID" field
    page.locator("#acm-search-field").select_option("id")
    # Search
    page.locator("#acm-search-input").fill("100201")
    page.wait_for_timeout(500)
    # Verify results filtered by ID only

def test_search_by_title(admin_page):
    """Test searching by title."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    page.locator("button:has-text('Add Courses')").first.click()
    page.locator("#acm-search-field").select_option("title")
    page.locator("#acm-search-input").fill("Computer")
    page.wait_for_timeout(500)
    # Results should contain "Computer" in title

def test_search_by_department(admin_page):
    """Test searching by department."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    page.locator("button:has-text('Add Courses')").first.click()
    page.locator("#acm-search-field").select_option("department")
    page.locator("#acm-search-input").fill("Mathematics")
    page.wait_for_timeout(500)
    # Results should be from Mathematics dept
```

---

## Feature 4: Batch Import Modes

### 4.1 Current State

The batch page has ID mode but catalog mode needs full implementation.

### 4.2 Needed Implementation

**Catalog Mode Functionality:**
- Pre-loaded catalog data on page
- Client-side filtering
- Select courses from dropdown/search
- Add to staging without API calls

### 4.3 Playwright Tests

```python
# tests/e2e/test_batch_catalog.py

def test_batch_catalog_mode_search(admin_page):
    """Test batch catalog search mode."""
    page = admin_page
    page.goto("/batch/")
    # Select catalog mode
    page.locator("input[value='catalog']").check()
    # Search in catalog
    page.locator("#batch-catalog-search").fill("CS")
    page.wait_for_timeout(500)
    # Verify catalog results appear

def test_batch_catalog_add_to_staging(admin_page):
    """Test adding catalog items to staging."""
    page = admin_page
    page.goto("/batch/")
    page.locator("input[value='catalog']").check()
    # Search and select
    page.locator("#batch-catalog-search").fill("CS50")
    page.wait_for_timeout(500)
    page.locator(".catalog-result").first.click()
    # Verify added to staging
    expect(page.locator("#batch-staged-courses")).to_contain_text("CS50")
```

---

## Feature 5: Additional Test Coverage

### 5.1 Security Tests

```python
# tests/e2e/test_security.py

def test_api_course_list_create_requires_admin(page):
    """Test course list creation requires admin."""
    response = page.request.post(
        "http://localhost:9223/aar/course-lists/",
        data={"name": "Test", "description": "Test"}
    )
    # Should return 403 without auth

def test_api_course_list_delete_requires_admin(page):
    """Test course list deletion requires admin."""
    response = page.request.delete(
        "http://localhost:9223/aar/course-lists/list-cs-core/"
    )
    # Should return 403

def test_csv_export_requires_admin(dept_page):
    """Test CSV export requires admin."""
    page = dept_page
    response = page.request.get(
        f"http://localhost:8000/plans/{KNOWN_PLAN_ID}/export/"
    )
    # Should return 403

def test_search_api_requires_admin(dept_page):
    """Test search API requires admin."""
    page = dept_page
    response = page.request.get(
        "http://localhost:8000/api/courses/search/?q=CS"
    )
    # Should return 403
```

### 5.2 Input Validation Tests

```python
# tests/e2e/test_validation.py

def test_search_query_too_long(admin_page):
    """Test too-long search query returns error."""
    page = admin_page
    long_query = "x" * 500
    response = page.request.get(
        f"http://localhost:8000/api/courses/search/?q={long_query}"
    )
    # Should return 400

def test_malformed_json_returns_400(admin_page):
    """Test malformed JSON in POST body returns 400."""
    page = admin_page
    response = page.request.post(
        f"http://localhost:8000/plans/{KNOWN_PLAN_ID}/requirements/add/",
        data="not valid json"
    )
    assert response.status == 400

def test_course_list_name_required(admin_page):
    """Test course list name is required."""
    page = admin_page
    page.goto("/course-lists/")
    page.locator("button:has-text('Create New List')").click()
    # Leave name empty
    page.locator("#cl-save-btn").click()
    # Should show validation error
```

---

## Summary of Test Files to Create

| File | Tests | Description |
|------|-------|-------------|
| `test_course_lists.py` | 7 | Course Lists CRUD operations |
| `test_shared_updates.py` | 2 | Shared list sync functionality |
| `test_search_filtering.py` | 3 | Course search field filtering |
| `test_batch_catalog.py` | 2 | Batch catalog mode |
| `test_security.py` | 4 | RBAC and security tests |
| `test_validation.py` | 3 | Input validation tests |

**Total: 21 new tests**

---

## Implementation Order

1. **Course Lists API** (FastAPI) - 5 endpoints
2. **Course Lists UI** (Django templates) - 5 templates
3. **Course Lists Tests** - 7 tests
4. **Shared Updates** - API + UI + Tests
5. **Search Filtering** - API + UI + Tests
6. **Batch Catalog Mode** - Fix + Tests
7. **Security Tests** - 4 tests
8. **Validation Tests** - 3 tests
