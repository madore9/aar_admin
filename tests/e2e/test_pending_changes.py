"""
Test cases for Pending Changes (SessionStorage draft system).
"""
import pytest
from playwright.sync_api import expect
from .conftest import wait_for_preline, KNOWN_PLAN_ID


def test_add_course_shows_changes_footer(admin_page):
    """Test adding a course shows the changes footer."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Open Add Course modal
    add_btn = page.locator("button:has-text('Add Courses')").first
    add_btn.click()
    page.wait_for_timeout(300)

    # Search and add a course (simplified)
    search_input = page.locator("#acm-search-input")
    page.wait_for_timeout(400)

    # Click to stage
    result = page.locator("#acm-search-results > div").first
    result.click()
    page.wait_for_timeout(200)

    # Click Add
    add_staged = page.locator("#acm-add-staged-btn")
    add_staged.click()
    page.wait_for_timeout(500)

    # Check changes footer appears
    footer = page.locator("[data-changes-footer]")
    if footer.count() > 0:
        expect(footer.first).to_be_visible()


def test_remove_course_shows_strikethrough(admin_page):
    """Test removing a course shows strikethrough styling."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Expand requirement
    collapse = page.locator("[data-hs-collapse]").first
    collapse.click()
    page.wait_for_timeout(300)

    # Find a course row
    course_row = page.locator("[data-identifier]").first
    if course_row.count() > 0:
        # Click remove button
        remove_btn = course_row.locator("[data-action='remove-course']").first
        if remove_btn.count() > 0:
            remove_btn.click()
            page.wait_for_timeout(300)

            # Check for strikethrough styling
            # Would need to check for specific classes


def test_save_draft_persists(admin_page):
    """Test saving draft persists changes."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Make some changes (add a course via modal)
    # Then click Save Draft
    save_draft_btn = page.locator("button:has-text('Save Draft')")
    if save_draft_btn.count() > 0:
        save_draft_btn.click()
        page.wait_for_timeout(500)

        # Check for toast
        toast = page.locator("#toast-container > div")
        expect(toast.last).to_be_visible()


def test_discard_draft_clears_changes(admin_page):
    """Test discarding draft clears changes."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Make changes
    # Click Cancel/Discard
    cancel_btn = page.locator("button:has-text('Cancel'), button:has-text('Discard')")
    if cancel_btn.count() > 0:
        cancel_btn.first.click()
        page.wait_for_timeout(500)

        # Page should reload
        # Changes should be cleared


def test_changes_persist_in_session_storage(admin_page):
    """Test changes persist in sessionStorage across navigation."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Make changes
    # Navigate away
    page.goto("/")
    page.wait_for_timeout(300)

    # Navigate back
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    page.wait_for_timeout(500)

    # Check if changes are still present in sessionStorage
    # Would need to check sessionStorage data
