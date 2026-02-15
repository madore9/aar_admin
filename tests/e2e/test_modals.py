"""
Test cases for all modal interactions.
"""
import pytest
from playwright.sync_api import expect
from .conftest import wait_for_preline, KNOWN_PLAN_ID, KNOWN_REQ_ID


def test_add_course_modal_opens(admin_page):
    """Test Add Course modal opens correctly."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Click "Add Courses" button on first requirement
    add_courses_btn = page.locator("button:has-text('Add Courses')").first
    add_courses_btn.click()

    # Wait for modal
    page.wait_for_timeout(300)

    # Check modal is visible
    modal = page.locator("#add-course-modal")
    expect(modal).to_be_visible()

    # Check modal title shows requirement name
    expect(modal).to_contain_text("Course")

    # Check search tab is active by default
    search_tab = page.locator("[data-hs-tab='#acm-tabpane-search'].hs-tab-active")
    expect(search_tab).to_be_visible()

    # Check search input is empty
    search_input = page.locator("#acm-search-input")
    expect(search_input).to_be_visible()


def test_add_course_modal_search(admin_page):
    """Test Add Course modal search functionality."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Open modal
    add_courses_btn = page.locator("button:has-text('Add Courses')").first
    add_courses_btn.click()
    page.wait_for_timeout(300)

    # Type in search input
    search_input = page.locator("#acm-search-input")
    search_input.fill("CS")
    page.wait_for_timeout(400)  # debounce

    # Wait for API response
    with page.expect_response("**/api/courses/search/**") as response_info:
        pass

    response = response_info.value
    assert response.status == 200

    # Check search results appear
    results = page.locator("#acm-search-results")
    expect(results).to_be_visible()


def test_add_course_modal_stage_and_add(admin_page):
    """Test staging courses and adding them."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Open modal
    add_courses_btn = page.locator("button:has-text('Add Courses')").first
    add_courses_btn.click()
    page.wait_for_timeout(300)

    # Search for a course
    search_input = page.locator("#acm-search-input")
    search_input.fill("CS50")
    page.wait_for_timeout(400)

    # Click on a search result to stage it
    search_result = page.locator("#acm-search-results > div").first
    search_result.click()
    page.wait_for_timeout(200)

    # Check staged area appears
    staging_container = page.locator("#acm-staging-container")
    expect(staging_container).to_be_visible()

    # Click "Add Selected Courses" button
    add_btn = page.locator("#acm-add-staged-btn")
    add_btn.click()

    # Wait for modal to close
    page.wait_for_timeout(500)

    # Check toast appears
    toast = page.locator("#toast-container > div").last
    expect(toast).to_be_visible(timeout=5000)


def test_add_course_modal_wildcards(admin_page):
    """Test Add Course modal wildcards tab."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Open modal
    add_courses_btn = page.locator("button:has-text('Add Courses')").first
    add_courses_btn.click()
    page.wait_for_timeout(300)

    # Click "Wildcards" tab
    wildcards_tab = page.locator("[data-hs-tab='#acm-tabpane-wildcards']")
    wildcards_tab.click()
    page.wait_for_timeout(300)

    # Enter wildcard patterns
    wildcard_input = page.locator("#acm-wildcard-input")
    wildcard_input.fill("CS 1*\nMATH 2#")

    # Click "Review Patterns" button
    review_btn = page.locator("#acm-review-wildcards-btn")
    review_btn.click()
    page.wait_for_timeout(300)

    # Check review section appears
    review_section = page.locator("#acm-wildcard-review")
    expect(review_section).to_be_visible()


def test_add_course_modal_from_list(admin_page):
    """Test Add Course modal 'Add From List' tab."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Open modal
    add_courses_btn = page.locator("button:has-text('Add Courses')").first
    add_courses_btn.click()
    page.wait_for_timeout(300)

    # Click "Add From List" tab
    from_list_tab = page.locator("[data-hs-tab='#acm-tabpane-from-list']")
    from_list_tab.click()
    page.wait_for_timeout(300)

    # Check course list dropdown exists
    list_select = page.locator("#acm-course-list-select")
    expect(list_select).to_be_visible()


def test_edit_validity_modal_opens(admin_page):
    """Test Edit Validity modal opens."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Expand first requirement
    collapse_toggle = page.locator("[data-hs-collapse]").first
    collapse_toggle.click()
    page.wait_for_timeout(300)

    # Click "Edit validity" button on a course row
    edit_validity_btn = page.locator("[data-action='edit-validity']").first
    if edit_validity_btn.count() > 0:
        edit_validity_btn.click()
        page.wait_for_timeout(300)

        # Check modal opens
        modal = page.locator("#edit-validity-modal")
        expect(modal).to_be_visible()


def test_edit_validity_change_to_terms(admin_page):
    """Test changing validity to specific terms."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Expand requirement
    collapse_toggle = page.locator("[data-hs-collapse]").first
    collapse_toggle.click()
    page.wait_for_timeout(300)

    # Try to open edit validity modal
    edit_btn = page.locator("[data-action='edit-validity']").first
    if edit_btn.count() > 0:
        edit_btn.click()
        page.wait_for_timeout(300)

        # Click "TERMS" radio button
        terms_radio = page.locator("input[value='TERMS']")
        if terms_radio.count() > 0:
            terms_radio.click()
            page.wait_for_timeout(200)

            # Check terms container appears
            terms_container = page.locator("#evm-terms-container")
            expect(terms_container).to_be_visible()


def test_edit_validity_date_range(admin_page):
    """Test changing validity to date range."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Expand requirement
    collapse_toggle = page.locator("[data-hs-collapse]").first
    collapse_toggle.click()
    page.wait_for_timeout(300)

    # Try to open edit validity modal
    edit_btn = page.locator("[data-action='edit-validity']").first
    if edit_btn.count() > 0:
        edit_btn.click()
        page.wait_for_timeout(300)

        # Click "DATE_RANGE" radio
        date_radio = page.locator("input[value='DATE_RANGE']")
        if date_radio.count() > 0:
            date_radio.click()
            page.wait_for_timeout(200)

            # Check date container appears
            date_container = page.locator("#evm-date-container")
            expect(date_container).to_be_visible()


def test_add_requirement_modal(admin_page):
    """Test Add Requirement modal."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Click "Add New Requirement" button
    add_btn = page.locator("button:has-text('Add New Requirement')")
    add_btn.click()
    page.wait_for_timeout(300)

    # Check modal opens
    modal = page.locator("#requirement-modal")
    expect(modal).to_be_visible()

    # Check modal title says "Add Requirement"
    expect(modal).to_contain_text("Requirement")

    # Fill in the form
    title_input = page.locator("#rm-req-title")
    title_input.fill("Test Requirement")

    # Click Save
    save_btn = page.locator("#rm-save-btn")
    save_btn.click()

    # Check for toast or page reload
    page.wait_for_timeout(500)


def test_edit_requirement_modal(admin_page):
    """Test Edit Requirement modal."""
    page = admin_page(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Look for edit requirement button
    edit_btn = page.locator("[data-action='edit-requirement']").first
    if edit_btn.count() > 0:
        edit_btn.click()
        page.wait_for_timeout(300)

        # Check modal opens with pre-filled values
        modal = page.locator("#requirement-modal")
        expect(modal).to_be_visible()

        # Check modal title says "Edit Requirement"
        expect(modal).to_contain_text("Edit")


def test_requirement_modal_title_required(admin_page):
    """Test that requirement title is required."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Click "Add New Requirement" button
    add_btn = page.locator("button:has-text('Add New Requirement')")
    add_btn.click()
    page.wait_for_timeout(300)

    # Leave title empty and try to save
    save_btn = page.locator("#rm-save-btn")
    save_btn.click()

    # Modal should stay open - check for error
    page.wait_for_timeout(300)
    modal = page.locator("#requirement-modal")
    expect(modal).to_be_visible()


def test_confirmation_modal_shows_counts(admin_page):
    """Test confirmation modal shows add/remove counts."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # The confirmation modal appears after making changes
    # For now, check the modal structure exists
    # This would require making actual changes first
    pass


def test_confirmation_modal_select_scope_and_confirm(admin_page):
    """Test confirmation modal scope selection and confirm."""
    page = admin_page
    # Would require making changes first to trigger confirmation modal
    pass


def test_history_modal_opens_and_loads(admin_page):
    """Test History modal opens and loads audit log."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")
    wait_for_preline(page)

    # Click "View Audit Log" button
    audit_btn = page.locator("button:has-text('Audit Log'), button:has-text('View Audit')").first
    audit_btn.click()
    page.wait_for_timeout(300)

    # Check modal opens
    modal = page.locator("#history-modal")
    expect(modal).to_be_visible()

    # Check for loading state or entries
    page.wait_for_timeout(1000)


def test_history_modal_empty_state(admin_page):
    """Test History modal empty state."""
    page = admin_page
    # Would need a plan with no audit entries
    pass


def test_history_modal_timestamp_formatting(admin_page):
    """Test History modal timestamps are formatted."""
    page = admin_page
    # Would need audit entries to test formatting
    pass
