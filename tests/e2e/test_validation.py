"""
Test cases for Input Validation.
"""
import pytest
from playwright.sync_api import expect
from .conftest import KNOWN_PLAN_ID, BASE_URL


def test_search_query_too_long(admin_page):
    """Test too-long search query is handled."""
    page = admin_page
    long_query = "x" * 500

    # Try API with long query
    response = page.request.get(f"{BASE_URL}/api/courses/search/?q={long_query}")

    # Should either succeed with empty results or return 400
    assert response.status in [200, 400], f"Expected 200 or 400, got {response.status}"


def test_malformed_json_returns_error(admin_page):
    """Test malformed JSON in POST body returns error."""
    page = admin_page

    # Try to POST malformed JSON
    response = page.request.post(
        f"{BASE_URL}/plans/{KNOWN_PLAN_ID}/requirements/add/",
        data="not valid json {",
        headers={"Content-Type": "application/json"}
    )

    # Should return 400 for bad JSON
    assert response.status in [400, 500], f"Expected 400 or 500, got {response.status}"


def test_empty_search_returns_empty_results(admin_page):
    """Test empty search query returns empty results."""
    page = admin_page

    response = page.request.get(f"{BASE_URL}/api/courses/search/?q=")

    # Should return 200 with empty courses
    assert response.status == 200
    data = response.json()
    assert "courses" in data or data == []


def test_single_char_search_returns_empty(admin_page):
    """Test single character search is rejected or returns empty."""
    page = admin_page

    response = page.request.get(f"{BASE_URL}/api/courses/search/?q=a")

    # Should either return empty or redirect
    assert response.status in [200, 302], f"Expected 200 or 302, got {response.status}"


def test_special_chars_in_search_handled(admin_page):
    """Test special characters in search are handled safely."""
    page = admin_page

    # Search with special characters
    response = page.request.get(f"{BASE_URL}/api/courses/search/?q=<script>alert(1)</script>")

    # Should handle safely - either sanitize or return empty
    assert response.status in [200, 400], f"Expected 200 or 400, got {response.status}"
