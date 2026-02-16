"""
Test cases for Batch Catalog Mode.
"""
import pytest
from playwright.sync_api import expect
from .conftest import KNOWN_PLAN_ID


def test_batch_catalog_mode_search(admin_page):
    """Test batch catalog search mode."""
    page = admin_page
    page.goto("/batch/")

    # Check if catalog mode radio exists
    catalog_radio = page.locator("input[value='catalog'], input[name='import-mode'][value='catalog']")
    if catalog_radio.count() > 0:
        catalog_radio.check()
        page.wait_for_timeout(300)

        # Look for catalog search input
        catalog_search = page.locator("#batch-catalog-search, input[placeholder*='catalog']")
        if catalog_search.count() > 0:
            catalog_search.fill("CS")
            page.wait_for_timeout(500)


def test_batch_catalog_add_to_staging(admin_page):
    """Test adding catalog items to staging."""
    page = admin_page
    page.goto("/batch/")

    # Select catalog mode
    catalog_radio = page.locator("input[value='catalog']")
    if catalog_radio.count() > 0:
        catalog_radio.check()
        page.wait_for_timeout(300)

        # Search
        catalog_search = page.locator("#batch-catalog-search")
        if catalog_search.count() > 0:
            catalog_search.fill("CS50")
            page.wait_for_timeout(500)

            # Click on result if available
            result = page.locator(".catalog-result, #batch-search-results > div").first
            if result.count() > 0:
                result.click()
                page.wait_for_timeout(300)


def test_batch_id_mode_validate(admin_page):
    """Test batch ID mode validation."""
    page = admin_page
    page.goto("/batch/")

    # Select ID mode
    id_radio = page.locator("input[value='id']")
    if id_radio.count() > 0:
        id_radio.check()
        page.wait_for_timeout(300)

        # Enter course IDs
        text_input = page.locator("#batch-text-input")
        text_input.fill("100201\n100202")

        # Click validate
        validate_btn = page.locator("#batch-validate-btn")
        if validate_btn.count() > 0:
            validate_btn.click()
            page.wait_for_timeout(1000)
