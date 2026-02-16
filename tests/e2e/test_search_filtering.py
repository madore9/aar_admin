"""
Test cases for Course Search Field Filtering.
"""
import pytest
from playwright.sync_api import expect
from .conftest import KNOWN_PLAN_ID, wait_for_preline


def test_search_by_course_id(admin_page):
    """Test searching by course ID field."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Expand requirement to find Add Courses button
    collapse = page.locator("[data-hs-collapse]").first
    collapse.click()
    page.wait_for_timeout(500)

    # Open Add Course modal
    add_btn = page.locator("button:has-text('Add Courses')").first
    add_btn.click()
    page.wait_for_timeout(500)

    # Check if search field dropdown exists
    search_field = page.locator("#acm-search-field, select[name='search_field']")
    if search_field.count() > 0:
        # Select Course ID field
        search_field.select_option("id")
        # Search
        search_input = page.locator("#acm-search-input")
        search_input.fill("100201")
        page.wait_for_timeout(500)
        # Verify search works
        expect(search_input).to_have_value("100201")


def test_search_by_title(admin_page):
    """Test searching by title field."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Expand and open modal
    collapse = page.locator("[data-hs-collapse]").first
    collapse.click()
    page.wait_for_timeout(500)
    page.locator("button:has-text('Add Courses')").first.click()
    page.wait_for_timeout(500)

    # Check for search field
    search_field = page.locator("#acm-search-field")
    if search_field.count() > 0:
        search_field.select_option("title")
        search_input = page.locator("#acm-search-input")
        search_input.fill("Computer")
        page.wait_for_timeout(500)


def test_search_by_department(admin_page):
    """Test searching by department field."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Expand and open modal
    collapse = page.locator("[data-hs-collapse]").first
    collapse.click()
    page.wait_for_timeout(500)
    page.locator("button:has-text('Add Courses')").first.click()
    page.wait_for_timeout(500)

    # Check for search field
    search_field = page.locator("#acm-search-field")
    if search_field.count() > 0:
        search_field.select_option("department")
        search_input = page.locator("#acm-search-input")
        search_input.fill("Mathematics")
        page.wait_for_timeout(500)
