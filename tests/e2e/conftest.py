"""
Shared fixtures for AAR Admin E2E tests.
All tests require both servers running: Django on :8000, FastAPI on :9223.
"""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8000"
FASTAPI_URL = "http://localhost:9223"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Set default browser context args."""
    return {
        **browser_context_args,
        "base_url": BASE_URL,
        "viewport": {"width": 1280, "height": 900},
    }


@pytest.fixture
def admin_page(page: Page) -> Page:
    """Page with ADMIN_USER role set via session cookie."""
    # First navigate to the home page to establish the session
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()

    # Use JavaScript to get CSRF token and make the request
    result = page.evaluate("""
        async () => {
            // First get csrftoken from cookie
            const cookies = document.cookie.split(';');
            let csrftoken = '';
            for (let c of cookies) {
                c = c.trim();
                if (c.startsWith('csrftoken=')) {
                    csrftoken = c.substring('csrftoken='.length);
                    break;
                }
            }

            // Make the request
            const formData = new URLSearchParams();
            formData.append('role', 'ADMIN_USER');

            const response = await fetch('/set-role/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrftoken
                },
                body: formData.toString(),
                credentials: 'include'
            });

            return {
                status: response.status,
                csrftoken: csrftoken,
                cookies: document.cookie
            };
        }
    """)

    # Reload to apply the session
    page.reload()
    page.wait_for_load_state()

    return page


@pytest.fixture
def dept_page(page: Page) -> Page:
    """Page with DEPT_USER role set (default role)."""
    page.goto("http://localhost:8000/")
    page.wait_for_load_state()
    return page


@pytest.fixture
def set_role(page: Page):
    """Helper fixture to switch roles mid-test."""
    def _set_role(role: str):
        # Use JavaScript to get CSRF token and make the request
        page.evaluate(f"""
            async () => {{
                // First get csrftoken from cookie
                const cookies = document.cookie.split(';');
                let csrftoken = '';
                for (let c of cookies) {{
                    c = c.trim();
                    if (c.startsWith('csrftoken=')) {{
                        csrftoken = c.substring('csrftoken='.length);
                        break;
                    }}
                }}

                // Make the request
                const formData = new URLSearchParams();
                formData.append('role', '{role}');

                await fetch('/set-role/', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrftoken
                    }},
                    body: formData.toString(),
                    credentials: 'include'
                }});
            }}
        """)

        # Reload to apply
        page.reload()
        page.wait_for_load_state()

        return page
    return _set_role


# Test data from seed_data.py
KNOWN_PLAN_ID = "plan-cs-conc"
KNOWN_PLAN_NAME = "Computer Science"
KNOWN_PLAN_TYPE = "Concentration"

# Requirements for plan-cs-conc
KNOWN_REQ_ID = "req-core"
KNOWN_REQ_TITLE = "Core Programming"

# Other plans
PLAN_CS_HONORS = "plan-cs-honors"
PLAN_CS_SECONDARY = "plan-cs-secondary"
PLAN_CS_JOINT = "plan-cs-joint"

# Known courses
KNOWN_COURSE_ID = "CS50"
KNOWN_SYSTEM_ID = "100201"  # CS50 - Introduction to Computer Science
KNOWN_COURSE_TITLE = "Introduction to Computer Science"

# Course lists
KNOWN_COURSE_LIST_ID = "list-cs-core"
KNOWN_COURSE_LIST_NAME = "CS Core Courses"


def wait_for_preline(page: Page):
    """Wait for Preline JS library to initialize."""
    page.wait_for_function("typeof HSOverlay !== 'undefined'")


def wait_for_toast(page: Page, text: str = None):
    """Wait for a toast notification to appear."""
    toast = page.locator("#toast-container > div").last
    expect(toast).to_be_visible(timeout=5000)
    if text:
        expect(toast).to_contain_text(text)
    return toast
