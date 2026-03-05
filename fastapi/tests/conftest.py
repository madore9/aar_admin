"""
Shared pytest fixtures for AAR Admin FastAPI tests.

Auth bypass:
  The FastAPI routes use Security(get_authenticated_user, scopes=[...]).
  In tests we override this dependency via app.dependency_overrides to skip
  the real X-API-Key check.

Oracle mock:
  We patch app.databases.oracle_db._pool at the module level.
  - mock_oracle_pool: pool is a non-None sentinel, oracle_query is patched
  - mock_no_oracle:   _pool is None (simulates no DSN / Oracle down)

SQLite:
  Tests use an in-memory aiosqlite DB via the existing init_db() function,
  but point DATABASE_PATH at :memory: via monkeypatching.
"""
import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import app.databases.oracle_db as oracle_db_module
from app.utils.security import get_authenticated_user, KeyPermissions


# ---------------------------------------------------------------------------
# Sample PS-shaped rows (as oracle_query would return them)
# ---------------------------------------------------------------------------
SAMPLE_ORACLE_ROWS = [
    {
        "system_id": "001234",
        "id":         "COMPSCI 50",
        "title":      "Introduction to Computer Science",
        "department": "COMPSCI",
        "credits":    4,
    },
    {
        "system_id": "002345",
        "id":         "MATH 21A",
        "title":      "Multivariable Calculus",
        "department": "MATH",
        "credits":    4,
    },
]

SAMPLE_ORACLE_SINGLE = [SAMPLE_ORACLE_ROWS[0]]


# ---------------------------------------------------------------------------
# Auth bypass fixture — overrides the Security dependency for all test routes
# ---------------------------------------------------------------------------
@pytest.fixture
def override_auth():
    """Yield a helper that installs an auth bypass on the given app instance."""

    def _install(app):
        async def _mock_user():
            return {"key": "test", "scopes": [p.value for p in KeyPermissions]}

        app.dependency_overrides[get_authenticated_user] = _mock_user
        yield app
        app.dependency_overrides.clear()

    return _install


# ---------------------------------------------------------------------------
# Oracle state fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_no_oracle(monkeypatch):
    """Simulate Oracle pool not being available (no DSN / pool = None)."""
    monkeypatch.setattr(oracle_db_module, "_pool", None)


@pytest.fixture
def mock_oracle_rows(monkeypatch):
    """Patch oracle_query to return SAMPLE_ORACLE_ROWS for any call."""

    async def _fake_query(sql, params=None):
        return list(SAMPLE_ORACLE_ROWS)

    # Set _pool to a truthy sentinel so "if _pool is None" checks pass
    monkeypatch.setattr(oracle_db_module, "_pool", object())
    monkeypatch.setattr(oracle_db_module, "oracle_query", _fake_query)
    # Also patch the import in courses.py (imported at module load)
    with patch("app.routers.courses.oracle_query", _fake_query):
        yield


@pytest.fixture
def mock_oracle_single(monkeypatch):
    """Patch oracle_query to return a single SAMPLE row."""

    async def _fake_query(sql, params=None):
        return list(SAMPLE_ORACLE_SINGLE)

    monkeypatch.setattr(oracle_db_module, "_pool", object())
    monkeypatch.setattr(oracle_db_module, "oracle_query", _fake_query)
    with patch("app.routers.courses.oracle_query", _fake_query):
        yield


@pytest.fixture
def mock_oracle_empty(monkeypatch):
    """Simulate Oracle pool available but query returns no rows."""

    async def _fake_query(sql, params=None):
        return []

    monkeypatch.setattr(oracle_db_module, "_pool", object())
    monkeypatch.setattr(oracle_db_module, "oracle_query", _fake_query)
    with patch("app.routers.courses.oracle_query", _fake_query):
        yield


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------
@pytest.fixture
def client():
    """Return a TestClient with auth bypassed and SQLite in-memory DB."""
    from app.main import app
    from app.utils.security import get_authenticated_user

    async def _mock_user(security_scopes=None, api_key=None):
        return {"key": "test", "scopes": [p.value for p in KeyPermissions]}

    app.dependency_overrides[get_authenticated_user] = _mock_user

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()
