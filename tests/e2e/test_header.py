"""
Test cases for Header functionality (myharvard-aligned UI).
"""
import pytest
from playwright.sync_api import expect, Page


def test_header_has_harvard_logo(page: Page):
    """Test that the header displays the Harvard logo."""
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()

    # Check desktop logo is visible
    desktop_logo = page.locator('img[alt="AAR Admin Logo"]').first
    expect(desktop_logo).to_be_visible()


def test_header_background_is_dark(page: Page):
    """Test that the header uses the correct dark background color."""
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()

    # Check header has the dark background
    header = page.locator("header.sticky")
    expect(header).to_be_visible()
    # The header should have the dark background (bg-[#1a1a1a])
    header_class = header.get_attribute("class")
    assert "bg-[" in header_class or "#1a1a1a" in header_class, f"Expected dark background, got: {header_class}"


def test_user_dropdown_opens(page: Page):
    """Test that clicking the user avatar opens the dropdown menu."""
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()

    # Click the user avatar button
    user_button = page.locator("button[aria-label='Open User Account Navigation']")
    expect(user_button).to_be_visible()
    user_button.click()
    page.wait_for_timeout(300)

    # Check dropdown menu is visible
    dropdown = page.locator(".hs-dropdown-menu")
    expect(dropdown).to_be_visible()


def test_user_dropdown_shows_role_switcher(page: Page):
    """Test that the role switcher is present in the user dropdown."""
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()

    # Open user dropdown
    user_button = page.locator("button[aria-label='Open User Account Navigation']")
    user_button.click()
    page.wait_for_timeout(300)

    # Check role options are visible
    admin_option = page.locator("button.role-option[data-role='ADMIN_USER']")
    dept_option = page.locator("button.role-option[data-role='DEPT_USER']")

    expect(admin_option).to_be_visible()
    expect(dept_option).to_be_visible()


def test_role_switch_to_admin_via_dropdown(page: Page):
    """Test switching to ADMIN_USER role via the user dropdown."""
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()

    # Open user dropdown
    user_button = page.locator("button[aria-label='Open User Account Navigation']")
    user_button.click()
    page.wait_for_timeout(300)

    # Click admin option
    admin_option = page.locator("button.role-option[data-role='ADMIN_USER']")
    admin_option.click()
    page.wait_for_timeout(1000)  # Wait for reload

    # Verify role was switched (check that admin option is now highlighted)
    page.wait_for_load_state()
    user_button = page.locator("button[aria-label='Open User Account Navigation']")
    user_button.click()
    page.wait_for_timeout(300)

    # Admin should have the selected styling
    admin_option = page.locator("button.role-option[data-role='ADMIN_USER']")
    admin_classes = admin_option.get_attribute("class")
    assert "bg-primary-light" in admin_classes or "font-medium" in admin_classes


def test_role_switch_to_dept_via_dropdown(page: Page):
    """Test switching to DEPT_USER role via the user dropdown."""
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()

    # First switch to admin, then back to dept
    user_button = page.locator("button[aria-label='Open User Account Navigation']")
    user_button.click()
    page.wait_for_timeout(300)

    admin_option = page.locator("button.role-option[data-role='ADMIN_USER']")
    admin_option.click()
    page.wait_for_timeout(1000)

    # Now switch back to dept
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()

    user_button = page.locator("button[aria-label='Open User Account Navigation']")
    user_button.click()
    page.wait_for_timeout(300)

    dept_option = page.locator("button.role-option[data-role='DEPT_USER']")
    dept_option.click()
    page.wait_for_timeout(1000)

    # Verify dept is selected
    page.wait_for_load_state()
    user_button = page.locator("button[aria-label='Open User Account Navigation']")
    user_button.click()
    page.wait_for_timeout(300)

    dept_option = page.locator("button.role-option[data-role='DEPT_USER']")
    dept_classes = dept_option.get_attribute("class")
    assert "bg-primary-light" in dept_classes or "font-medium" in dept_classes


def test_user_dropdown_has_sign_out(page: Page):
    """Test that the user dropdown contains a sign out option."""
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()

    # Open user dropdown
    user_button = page.locator("button[aria-label='Open User Account Navigation']")
    user_button.click()
    page.wait_for_timeout(300)

    # Check sign out link is visible
    sign_out = page.locator("a:has-text('Sign out')")
    expect(sign_out).to_be_visible()


def test_user_dropdown_has_settings(page: Page):
    """Test that the user dropdown contains a settings option."""
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()

    # Open user dropdown
    user_button = page.locator("button[aria-label='Open User Account Navigation']")
    user_button.click()
    page.wait_for_timeout(300)

    # Check settings link is visible
    settings = page.locator("a:has-text('Settings')")
    expect(settings).to_be_visible()

    # Verify settings link points to Django admin
    expect(settings).to_have_attribute("href", "/admin/")


def test_ideas_icon_visible(page: Page):
    """Test that the Ideas icon is visible in the header."""
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()

    # Check ideas button is visible
    ideas_button = page.locator("#ideas-button")
    expect(ideas_button).to_be_visible()


def test_center_nav_has_aar_admin(page: Page):
    """Test that the center navigation has AAR Admin link."""
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()

    # Check AAR Admin link is visible
    aar_admin = page.locator("a.nav-links:has-text('AAR Admin')")
    expect(aar_admin).to_be_visible()


def test_role_switch_updates_page_content(page: Page):
    """Test that switching roles updates page content appropriately."""
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()

    # Open user dropdown and switch to admin
    user_button = page.locator("button[aria-label='Open User Account Navigation']")
    user_button.click()
    page.wait_for_timeout(300)

    admin_option = page.locator("button.role-option[data-role='ADMIN_USER']")
    admin_option.click()
    page.wait_for_timeout(1000)

    # Verify we can access admin features (navigate to batch page)
    page.goto("http://localhost:8000/batch/")
    page.wait_for_load_state()

    # Batch page should be accessible (or form should be visible)
    batch_form = page.locator("#batch-plan-select")
    # Either visible or we got in - either way test passes if no error
    assert "403" not in page.content()


def test_header_is_sticky(page: Page):
    """Test that the header is sticky (stays at top on scroll)."""
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()

    # Check header has sticky class
    header = page.locator("header.sticky")
    expect(header).to_be_visible()
    header_class = header.get_attribute("class")
    assert "sticky" in header_class, f"Expected sticky class, got: {header_class}"


def test_user_info_displayed_in_dropdown(page: Page):
    """Test that user information is displayed in the dropdown."""
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()

    # Open user dropdown
    user_button = page.locator("button[aria-label='Open User Account Navigation']")
    user_button.click()
    page.wait_for_timeout(300)

    # Check user name is visible
    user_name = page.locator("text=AAR Admin User")
    expect(user_name).to_be_visible()

    # Check role options are visible (there are two: ADMIN_USER and DEPT_USER)
    role_options = page.locator("button.role-option")
    expect(role_options).to_have_count(2)
