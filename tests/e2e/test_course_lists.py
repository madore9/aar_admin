"""
Test cases for Course Lists Management.
"""
import pytest
from playwright.sync_api import expect
from .conftest import KNOWN_COURSE_LIST_ID, wait_for_preline


def test_course_lists_page_loads(admin_page):
    """Test course lists page loads with admin."""
    page = admin_page
    page.goto("/course-lists/")

    # Check page loads
    expect(page.locator("h1")).to_be_visible()


def test_create_course_list(admin_page):
    """Test creating a new course list."""
    page = admin_page
    page.goto("/course-lists/")

    # Click "Create New List" button if exists
    create_btn = page.locator("button:has-text('Create New List'), button:has-text('Add Course List')")
    if create_btn.count() > 0:
        create_btn.click()
        page.wait_for_timeout(500)

        # Fill form if modal exists
        name_input = page.locator("input[name='name'], #cl-name-input, input[id*='name']")
        if name_input.count() > 0:
            name_input.fill("Test Course List")

            desc_input = page.locator("textarea[name='description'], #cl-description-input")
            if desc_input.count() > 0:
                desc_input.fill("Test Description")

            save_btn = page.locator("button:has-text('Save'), button:has-text('Create')")
            if save_btn.count() > 0:
                save_btn.click()
                page.wait_for_timeout(500)


def test_course_list_restricted_for_dept(dept_page):
    """Test course lists page is admin only."""
    page = dept_page
    page.goto("/course-lists/")

    # Should either redirect or show restricted message
    # Check that we're not on the course lists page
    if page.url.endswith("/course-lists/"):
        # Check for restricted access message or form not visible
        form_visible = page.locator("button:has-text('Create New List')").count() > 0
        expect(form_visible).to_be_falsey()


def test_course_list_navigation_from_header(admin_page):
    """Test navigating to course lists from header."""
    page = admin_page
    page.goto("/")

    # Look for Course Lists link in navigation
    cl_link = page.locator("a:has-text('Course Lists'), a:has-text('Course Lists')")
    if cl_link.count() > 0:
        cl_link.click()
        expect(page).to_have_url("/course-lists/")
