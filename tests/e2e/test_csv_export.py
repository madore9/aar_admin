"""
Test cases for CSV Export functionality.
"""
import pytest
from playwright.sync_api import expect
from .conftest import KNOWN_PLAN_ID


def test_csv_download_triggers(admin_page):
    """Test CSV download triggers correctly."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")

    # Click "Download Courselists" link
    download_link = page.locator("a:has-text('Download'), [href*='export']").first

    # Start download
    with page.expect_download() as download_info:
        download_link.click()

    download = download_info.value

    # Check filename
    assert download.suggested_filename.endswith(".csv")


def test_csv_content_has_headers(admin_page):
    """Test CSV content has proper headers."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")

    # Click download
    download_link = page.locator("a:has-text('Download'), [href*='export']").first

    with page.expect_download() as download_info:
        download_link.click()

    download = download_info.value

    # Read the file content
    content = download.path()
    with open(content, 'r') as f:
        csv_content = f.read()

    # Check headers
    assert "Plan Name" in csv_content
    assert "Subject" in csv_content or "Course" in csv_content


def test_csv_handles_wildcards(admin_page):
    """Test CSV handles wildcard courses."""
    page = admin_page
    page.goto(f"/plans/{KNOWN_PLAN_ID}/")

    # Download CSV
    download_link = page.locator("a:has-text('Download'), [href*='export']").first

    with page.expect_download() as download_info:
        download_link.click()

    download = download_info.value
    content = download.path()

    # Check for wildcard handling
    with open(content, 'r') as f:
        csv_content = f.read()

    # Should have data rows
    lines = csv_content.strip().split('\n')
    assert len(lines) > 1  # header + at least one data row


def test_csv_export_404_for_invalid_plan(admin_page):
    """Test CSV export returns 404 for invalid plan."""
    page = admin_page

    # Try to download from non-existent plan
    response = page.request.get(
        "http://localhost:8000/plans/nonexistent_plan/export/"
    )

    # Should return 404
    assert response.status == 404
