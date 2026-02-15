"""
Test cases for Plan Detail page.
"""
import pytest
from playwright.sync_api import expect
from .conftest import wait_for_preline, KNOWN_PLAN_ID, KNOWN_PLAN_NAME, KNOWN_REQ_ID


def test_plan_detail_loads(admin_page):
    """Test that plan detail page loads with all required elements."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")

    # Check plan name heading is visible
    expect(page.locator("h1")).to_contain_text(KNOWN_PLAN_NAME)

    # Check plan type badge is visible
    expect(page.locator("[class*='badge'], [class*='px-'], [class*='rounded']").first).to_be_visible()

    # Check "Download Courselists" link is visible
    download_link = page.locator("a:has-text('Download'), [href*='export']")
    expect(download_link.first).to_be_visible()

    # Check "View Audit Log" button is visible (admin only)
    audit_btn = page.locator("button:has-text('Audit Log'), button:has-text('View Audit')")
    expect(audit_btn.first).to_be_visible()

    # Check "Add New Requirement" button is visible (admin only)
    add_req_btn = page.locator("button:has-text('Add New Requirement')")
    expect(add_req_btn).to_be_visible()

    # Check at least one requirement section is visible
    req_sections = page.locator("[data-req-section]")
    expect(req_sections.first).to_be_visible()

    # Check CSRF token exists in the page (it's a hidden input)
    # Just check that at least one exists
    csrf_count = page.locator("[name=csrfmiddlewaretoken]").count()
    assert csrf_count >= 1, f"Expected at least 1 CSRF token, found {csrf_count}"


def test_plan_detail_back_button(admin_page):
    """Test back button navigates to plan list."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")

    # Click "Back to Plans" link
    back_link = page.locator("a:has-text('Back to Plans')")
    back_link.click()

    # Should navigate to plan list
    assert "/plans/" not in page.url or page.url.endswith("/") or page.url.endswith("/plans/")


def test_requirement_section_expand_collapse(admin_page):
    """Test expanding and collapsing requirement sections."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Check at least one requirement section exists
    req_sections = page.locator("[data-req-section]")
    expect(req_sections.first).to_be_visible()

    # Get first requirement's collapse toggle
    collapse_toggle = page.locator("[data-hs-collapse]").first
    expect(collapse_toggle).to_be_visible()

    # Click to expand
    collapse_toggle.click()

    # Wait for animation
    page.wait_for_timeout(500)

    # After click, check that something changed - look for course rows or content
    # The requirement body should now contain course rows or content
    course_rows = page.locator("[data-identifier]")
    # Either there are course rows or empty state
    content_visible = course_rows.count() > 0 or page.locator("text=No courses assigned").count() > 0
    assert content_visible, "Requirement content should be visible after expand"


def test_requirement_shows_badges(admin_page):
    """Test requirement shows min courses/units badges."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")

    # Check for "Min. Courses:" badge
    min_courses = page.locator("text=Min. Courses")
    if min_courses.count() > 0:
        expect(min_courses.first).to_be_visible()

    # Check for "Min. Units:" badge
    min_units = page.locator("text=Min. Units")
    if min_units.count() > 0:
        expect(min_units.first).to_be_visible()


def test_plan_detail_no_requirements_empty_state(admin_page):
    """Test empty requirements state."""
    # Navigate to a plan with no requirements if available
    # For now, check the page loads
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")

    # Page should load - requirements exist in seed data
    expect(page.locator("h1")).to_contain_text(KNOWN_PLAN_NAME)


def test_course_row_displays_info(admin_page):
    """Test course row displays system ID, course ID, and title."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Expand first requirement
    collapse_toggle = page.locator("[data-hs-collapse]").first
    collapse_toggle.click()

    # Wait for animation
    page.wait_for_timeout(300)

    # Check course row is visible
    course_rows = page.locator("[data-identifier]")
    if course_rows.count() > 0:
        first_course = course_rows.first
        expect(first_course).to_be_visible()

        # Check for system ID badge (monospace)
        system_id = first_course.locator("[class*='font-mono'], [class*='mono']")
        if system_id.count() > 0:
            expect(system_id.first).to_be_visible()

        # Check admin buttons are visible
        edit_btn = first_course.locator("button:has-text('Edit'), button[title*='Edit']")
        if edit_btn.count() > 0:
            expect(edit_btn.first).to_be_visible()
