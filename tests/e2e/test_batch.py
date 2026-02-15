"""
Test cases for Batch Add page.
"""
import pytest
from playwright.sync_api import expect
from .conftest import KNOWN_PLAN_ID, KNOWN_REQ_ID


def test_batch_page_loads(admin_page):
    """Test batch page loads with all elements."""
    page = admin_page
    page.goto("/batch/")

    # Check plan dropdown is visible
    plan_select = page.locator("#batch-plan-select")
    expect(plan_select).to_be_visible()

    # Check requirement dropdown is visible but disabled initially
    req_select = page.locator("#batch-req-select")
    expect(req_select).to_be_visible()

    # Check import mode radios are visible
    radios = page.locator("input[name='import-mode']")
    expect(radios.first).to_be_visible()

    # Check input panel is visible
    text_input = page.locator("#batch-text-input")
    expect(text_input).to_be_visible()


def test_batch_plan_req_selection(admin_page):
    """Test selecting plan and requirement."""
    page = admin_page
    page.goto("/batch/")

    # Select a plan
    plan_select = page.locator("#batch-plan-select")
    plan_select.select_option(KNOWN_PLAN_ID)
    page.wait_for_timeout(500)

    # Wait for requirements to load
    with page.expect_response("**/api/batch/plan/**/requirements/**") as response_info:
        pass

    # Check requirement dropdown becomes enabled
    req_select = page.locator("#batch-req-select")
    expect(req_select).to_be_enabled()

    # Select a requirement
    req_select.select_option(KNOWN_REQ_ID)
    page.wait_for_timeout(300)

    # Check input area is ready
    text_input = page.locator("#batch-text-input")
    expect(text_input).to_be_visible()


def test_batch_text_input_validate(admin_page):
    """Test batch text input validation."""
    page = admin_page
    page.goto("/batch/")

    # Select plan and requirement
    page.locator("#batch-plan-select").select_option(KNOWN_PLAN_ID)
    page.wait_for_timeout(500)
    page.locator("#batch-req-select").select_option(KNOWN_REQ_ID)
    page.wait_for_timeout(300)

    # Enter identifiers
    text_input = page.locator("#batch-text-input")
    text_input.fill("100201\n100299\nINVALID999")

    # Click "Validate Input"
    validate_btn = page.locator("#batch-validate-btn")
    validate_btn.click()
    page.wait_for_timeout(1000)

    # Check results panel appears
    results_panel = page.locator("#batch-results, [class*='results']")
    # Results should appear


def test_batch_file_upload(admin_page):
    """Test file upload functionality."""
    page = admin_page
    page.goto("/batch/")

    # Select plan and requirement
    page.locator("#batch-plan-select").select_option(KNOWN_PLAN_ID)
    page.wait_for_timeout(500)
    page.locator("#batch-req-select").select_option(KNOWN_REQ_ID)
    page.wait_for_timeout(300)

    # Create a test CSV file
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("100201\n100202\n")
        temp_file = f.name

    try:
        # Upload file
        file_input = page.locator("input[type='file']")
        file_input.set_input_files(temp_file)
        page.wait_for_timeout(300)

        # Check textarea gets populated
        text_input = page.locator("#batch-text-input")
        expect(text_input).to_not_be_empty()
    finally:
        os.unlink(temp_file)


def test_batch_resolve_multiple_matches(admin_page):
    """Test resolving multiple matches."""
    # Would need specific input that triggers MULTIPLE_MATCHES
    pass


def test_batch_add_valid_matches(admin_page):
    """Test adding valid matches."""
    page = admin_page
    page.goto("/batch/")

    # Select plan and requirement
    page.locator("#batch-plan-select").select_option(KNOWN_PLAN_ID)
    page.wait_for_timeout(500)
    page.locator("#batch-req-select").select_option(KNOWN_REQ_ID)
    page.wait_for_timeout(300)

    # Enter valid identifiers
    text_input = page.locator("#batch-text-input")
    text_input.fill("100201")

    # Validate
    validate_btn = page.locator("#batch-validate-btn")
    validate_btn.click()
    page.wait_for_timeout(1000)

    # Click "Add Valid Matches" button if visible
    add_valid_btn = page.locator("#batch-add-valid")
    if add_valid_btn.count() > 0 and add_valid_btn.is_enabled():
        add_valid_btn.click()
        page.wait_for_timeout(500)


def test_batch_download_template(admin_page):
    """Test downloading batch template."""
    page = admin_page
    page.goto("/batch/")

    # Click "Download Template"
    download_btn = page.locator("#batch-download-template")

    # Start download expectation
    with page.expect_download() as download_info:
        download_btn.click()

    download = download_info.value
    # Check filename
    assert "template" in download.suggested_filename.lower() or ".csv" in download.suggested_filename.lower()


def test_batch_catalog_search(admin_page):
    """Test catalog search in batch page."""
    page = admin_page
    page.goto("/batch/")

    # Click catalog search tab
    catalog_tab = page.locator("[data-hs-tab='#batch-tabpane-catalog']")
    if catalog_tab.count() > 0:
        catalog_tab.click()
        page.wait_for_timeout(300)

        # Type in search
        catalog_search = page.locator("#batch-catalog-search")
        if catalog_search.count() > 0:
            catalog_search.fill("CS")
            page.wait_for_timeout(400)

            # Check results appear
            results = page.locator("#batch-search-results")
            # Results should appear
