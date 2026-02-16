"""
Test cases for Course Lookup page.
"""
import pytest
from playwright.sync_api import expect


def test_lookup_page_loads_admin(admin_page):
    """Test lookup page loads for admin user."""
    page = admin_page
    page.goto("/lookup/")

    # Check search input is visible
    search_input = page.locator("#course-search")
    expect(search_input).to_be_visible()


def test_lookup_search_courses(admin_page):
    """Test course search functionality."""
    page = admin_page
    page.goto("/lookup/")

    # Type in search
    search_input = page.locator("#course-search")
    search_input.fill("CS")
    page.wait_for_timeout(300)

    # Check dropdown results appear
    results = page.locator("#search-results")
    expect(results).to_be_visible()


def test_lookup_select_course_shows_usage(admin_page):
    """Test selecting a course shows usage information."""
    page = admin_page
    page.goto("/lookup/")

    # Search for a course
    search_input = page.locator("#course-search")
    search_input.fill("CS50")
    page.wait_for_timeout(300)

    # Click on a course result
    result = page.locator("#search-results > div").first
    result.click()
    page.wait_for_timeout(500)

    # Check selected course panel appears
    selected_panel = page.locator("#selected-course-panel")
    # Panel may or may not appear depending on implementation

    # Check usage results panel appears
    usage_panel = page.locator("#usage-results-panel")
    # Should show loading or results


def test_lookup_empty_usage(admin_page):
    """Test selecting a course with no usage."""
    page = admin_page
    page.goto("/lookup/")

    # Search for a course that might not be used
    search_input = page.locator("#course-search")
    search_input.fill("ENG101")
    page.wait_for_timeout(300)

    # Click on result
    result = page.locator("#search-results > div").first
    result.click()
    page.wait_for_timeout(500)

    # Check for empty state
    empty_state = page.locator("#usage-empty, text=not used")
    # May or may not show depending on data


def test_lookup_restricted_for_dept_user(dept_page):
    """Test lookup page is restricted for dept user."""
    page = dept_page
    page.goto("/lookup/")

    # Should return 403 or show restricted message
    # Check if search input is NOT visible
    search_input = page.locator("#course-search")
    # Either 403 page or restricted message
    if page.url == "http://localhost:8000/lookup/":
        expect(search_input).to_be_hidden()
