"""
Test cases for Security - RBAC enforcement on all endpoints.
"""
import pytest
from playwright.sync_api import expect
from .conftest import KNOWN_PLAN_ID, BASE_URL, FASTAPI_URL


def test_api_course_search_requires_admin(dept_page):
    """Test course search API requires admin."""
    page = dept_page

    # Try to access search API
    response = page.request.get(f"{BASE_URL}/api/courses/search/?q=CS")

    # Should return 403 or redirect
    assert response.status in [403, 302], f"Expected 403 or 302, got {response.status}"


def test_api_course_list_detail_requires_admin(dept_page):
    """Test course list detail API requires admin."""
    page = dept_page

    response = page.request.get(f"{BASE_URL}/api/course-lists/list-cs-core/")

    # Should return 403 or redirect
    assert response.status in [403, 302, 404], f"Expected 403/302/404, got {response.status}"


def test_csv_export_requires_admin(dept_page):
    """Test CSV export requires admin."""
    page = dept_page

    response = page.request.get(f"{BASE_URL}/plans/{KNOWN_PLAN_ID}/export/")

    # Should return 403 or redirect
    assert response.status in [403, 302], f"Expected 403 or 302, got {response.status}"


def test_course_lists_page_requires_admin(dept_page):
    """Test course lists page requires admin."""
    page = dept_page

    page.goto("/course-lists/")

    # Should either redirect or show restricted access
    if page.url.endswith("/course-lists/"):
        # Check for restricted content
        restricted = page.locator("text=Access Denied, text=Forbidden, text=403").count()
        expect(restricted).to_be_greater_than(0)


def test_batch_page_requires_admin_strict(dept_page):
    """Test batch page properly requires admin."""
    page = dept_page

    page.goto("/batch/")

    # Should redirect or show 403
    # Verify batch form is not accessible
    batch_form = page.locator("#batch-plan-select, form[action*='batch']")
    if batch_form.count() > 0:
        # If form exists, check it's not functional
        expect(page.locator("body")).to_contain_text("Access Denied")


def test_lookup_page_requires_admin_strict(dept_page):
    """Test lookup page properly requires admin."""
    page = dept_page

    page.goto("/lookup/")

    # Should redirect or show 403
    search_input = page.locator("#course-search")
    # Either redirect happened or search is hidden
    if page.url.endswith("/lookup/"):
        expect(search_input).to_be_hidden()
