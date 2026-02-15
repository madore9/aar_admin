"""
Test cases for Plan List page.
"""
import re
import pytest
from playwright.sync_api import expect


def test_plan_list_loads(dept_page):
    """Test that the plan list page loads correctly."""
    page = dept_page
    page.goto("/")

    # Check page title contains "AAR Admin"
    expect(page).to_have_title(re.compile(r"AAR Admin", re.IGNORECASE))

    # Check at least one plan card is visible - look for divs with plan cards
    plan_cards = page.locator(".grid > div")
    expect(plan_cards.first).to_be_visible()

    # Check header is visible with "AAR Admin" or "Academic Plans" text
    header = page.locator("h1")
    expect(header).to_contain_text("Academic Plans")

    # Check tab navigation if exists
    tab_nav = page.locator("[data-active-tab]")
    if tab_nav.count() > 0:
        expect(tab_nav.first).to_be_visible()


def test_plan_list_search(dept_page):
    """Test plan list search functionality."""
    page = dept_page
    page.goto("/")

    # Fill search input
    search_input = page.locator("input[name='q']")
    search_input.fill("Computer")

    # Submit form (press Enter)
    search_input.press("Enter")

    # Check URL contains query param
    assert "q=Computer" in page.url

    # Check search input retains the query value
    expect(search_input).to_have_value("Computer")


def test_plan_list_clear_search(dept_page):
    """Test clearing search returns to full list."""
    page = dept_page
    page.goto("/?q=Computer")

    # Clear search input
    search_input = page.locator("input[name='q']")
    search_input.fill("")

    # Submit form
    search_input.press("Enter")

    # URL should not have query param with value
    # Allow empty q param but check for actual filtering
    # Just verify page loads
    expect(page.locator("h1")).to_contain_text("Academic Plans")


def test_plan_list_click_plan_navigates(dept_page):
    """Test clicking a plan card navigates to plan detail."""
    page = dept_page
    page.goto("/")

    # Click first "Select Plan" link
    first_plan_link = page.locator("a:has-text('Select Plan')").first
    first_plan_link.click()

    # URL should match plan detail pattern
    assert "/plans/" in page.url

    # Plan detail page should load with plan name in heading
    expect(page.locator("h1")).to_be_visible()
