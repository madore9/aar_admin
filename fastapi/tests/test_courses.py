"""
Integration tests for GET /aar/courses/ and GET /aar/courses/{system_id}.

Tests the dual-path logic: Oracle → SQLite fallback.
No real Oracle or Redis connection required — both are mocked/disabled.

Run with: cd fastapi && python -m pytest tests/test_courses.py -v
"""
import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import app.databases.oracle_db as oracle_db_module
from app.utils.security import get_authenticated_user, KeyPermissions


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------
ORACLE_ROWS = [
    {"system_id": "001234", "id": "COMPSCI 50",  "title": "Introduction to Computer Science", "department": "COMPSCI", "credits": 4},
    {"system_id": "002345", "id": "MATH 21A",    "title": "Multivariable Calculus",            "department": "MATH",    "credits": 4},
    {"system_id": "003456", "id": "ECON 10A",    "title": "Principles of Economics",           "department": "ECON",    "credits": 4},
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def disable_cache(monkeypatch):
    """Disable FastAPI-cache for all tests so caching doesn't interfere."""
    async def _passthrough(func, *args, **kwargs):
        return await func(*args, **kwargs)

    with patch("fastapi_cache.decorator.cache", lambda *a, **kw: lambda f: f):
        yield


@pytest.fixture
def app_client():
    """TestClient with auth bypassed."""
    from app.main import app

    async def _mock_auth(security_scopes=None, api_key=None):
        return {"key": "test", "scopes": [p.value for p in KeyPermissions]}

    app.dependency_overrides[get_authenticated_user] = _mock_auth
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def oracle_available(monkeypatch):
    """Oracle pool is available; oracle_query returns ORACLE_ROWS."""
    async def _fake_query(sql, params=None):
        return list(ORACLE_ROWS)

    monkeypatch.setattr(oracle_db_module, "_pool", object())
    with patch("app.routers.courses.oracle_query", _fake_query):
        yield


@pytest.fixture
def oracle_unavailable(monkeypatch):
    """Oracle pool is None (local dev / no DSN)."""
    monkeypatch.setattr(oracle_db_module, "_pool", None)


@pytest.fixture
def oracle_available_filtered(monkeypatch):
    """Oracle returns only COMPSCI courses (simulates a search filter response)."""
    async def _fake_query(sql, params=None):
        return [r for r in ORACLE_ROWS if r["department"] == "COMPSCI"]

    monkeypatch.setattr(oracle_db_module, "_pool", object())
    with patch("app.routers.courses.oracle_query", _fake_query):
        yield


@pytest.fixture
def oracle_available_single(monkeypatch):
    """Oracle returns exactly one course for single-lookup tests."""
    async def _fake_query(sql, params=None):
        return [ORACLE_ROWS[0]]

    monkeypatch.setattr(oracle_db_module, "_pool", object())
    with patch("app.routers.courses.oracle_query", _fake_query):
        yield


@pytest.fixture
def oracle_available_empty(monkeypatch):
    """Oracle pool is set but query returns no rows (course not found)."""
    async def _fake_query(sql, params=None):
        return []

    monkeypatch.setattr(oracle_db_module, "_pool", object())
    with patch("app.routers.courses.oracle_query", _fake_query):
        yield


# ---------------------------------------------------------------------------
# GET /aar/courses/ — Oracle path
# ---------------------------------------------------------------------------

def test_search_courses_uses_oracle_when_available(app_client, oracle_available):
    """When Oracle is available, the response should contain Oracle rows."""
    resp = app_client.get("/aar/courses/", headers={"X-API-Key": "dev-key-123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == len(ORACLE_ROWS)
    ids = {c["id"] for c in data["courses"]}
    assert "COMPSCI 50" in ids
    assert "MATH 21A" in ids


def test_search_courses_returns_correct_schema_fields(app_client, oracle_available):
    """Every course in the response must have all 5 required fields."""
    resp = app_client.get("/aar/courses/", headers={"X-API-Key": "dev-key-123"})
    assert resp.status_code == 200
    for course in resp.json()["courses"]:
        assert "system_id"  in course
        assert "id"         in course
        assert "title"      in course
        assert "department" in course
        assert "credits"    in course


def test_search_courses_search_filter_returns_subset(app_client, oracle_available_filtered):
    """When ?q= is provided, filtered results should be returned."""
    resp = app_client.get("/aar/courses/?q=compsci&field=department", headers={"X-API-Key": "dev-key-123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["courses"][0]["department"] == "COMPSCI"


def test_search_courses_total_matches_courses_length(app_client, oracle_available):
    """total field must always equal len(courses)."""
    resp = app_client.get("/aar/courses/", headers={"X-API-Key": "dev-key-123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == len(data["courses"])


# ---------------------------------------------------------------------------
# GET /aar/courses/ — SQLite fallback path
# ---------------------------------------------------------------------------

def test_search_courses_falls_back_to_sqlite_when_oracle_unavailable(app_client, oracle_unavailable):
    """When Oracle pool is None, the endpoint must return seed data without error."""
    resp = app_client.get("/aar/courses/", headers={"X-API-Key": "dev-key-123"})
    # Seed data may be empty in test environment, but should not 500
    assert resp.status_code == 200
    data = resp.json()
    assert "courses" in data
    assert "total"   in data


def test_search_courses_sqlite_fallback_total_matches_courses(app_client, oracle_unavailable):
    """Fallback total must still equal len(courses)."""
    resp = app_client.get("/aar/courses/", headers={"X-API-Key": "dev-key-123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == len(data["courses"])


# ---------------------------------------------------------------------------
# GET /aar/courses/{system_id} — Oracle path
# ---------------------------------------------------------------------------

def test_get_course_by_system_id_oracle_path(app_client, oracle_available_single):
    """Single course lookup should return the correct course from Oracle."""
    resp = app_client.get("/aar/courses/001234", headers={"X-API-Key": "dev-key-123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["system_id"] == "001234"
    assert data["id"]        == "COMPSCI 50"
    assert data["title"]     == "Introduction to Computer Science"
    assert data["department"] == "COMPSCI"
    assert data["credits"]   == 4


def test_get_course_returns_404_when_oracle_returns_nothing(app_client, oracle_available_empty):
    """When Oracle is available but course not found, return 404."""
    resp = app_client.get("/aar/courses/NOTEXIST", headers={"X-API-Key": "dev-key-123"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /aar/courses/{system_id} — SQLite fallback path
# ---------------------------------------------------------------------------

def test_get_course_falls_back_to_sqlite(app_client, oracle_unavailable):
    """When Oracle is unavailable, single lookup uses SQLite seed data."""
    resp = app_client.get("/aar/courses/CS50", headers={"X-API-Key": "dev-key-123"})
    # Seed data may not have CS50 in test env — expect either 200 or 404, never 500
    assert resp.status_code in (200, 404)


def test_get_course_sqlite_fallback_404_for_missing(app_client, oracle_unavailable):
    """404 must be returned for a missing course even on the SQLite fallback path."""
    resp = app_client.get("/aar/courses/DEFINITELY_NOT_A_REAL_COURSE_ID_XYZ", headers={"X-API-Key": "dev-key-123"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

def test_search_courses_requires_auth(app_client):
    """Without overriding auth, missing API key returns 403."""
    from app.main import app
    app.dependency_overrides.clear()  # Remove auth bypass
    with TestClient(app, raise_server_exceptions=True) as c:
        resp = c.get("/aar/courses/")
    assert resp.status_code in (401, 403, 422)
    # Re-apply bypass for subsequent tests
    async def _mock_auth(security_scopes=None, api_key=None):
        return {"key": "test", "scopes": [p.value for p in KeyPermissions]}
    app.dependency_overrides[get_authenticated_user] = _mock_auth


# ---------------------------------------------------------------------------
# Data coercion
# ---------------------------------------------------------------------------

def test_oracle_row_with_decimal_credits_coerced_to_int(app_client, monkeypatch):
    """Credits coming back as Decimal from Oracle must be converted to int."""
    from decimal import Decimal

    async def _fake_query(sql, params=None):
        return [{"system_id": "001234", "id": "COMPSCI 50", "title": "Intro", "department": "CS", "credits": Decimal("4.0")}]

    monkeypatch.setattr(oracle_db_module, "_pool", object())
    with patch("app.routers.courses.oracle_query", _fake_query):
        resp = app_client.get("/aar/courses/001234", headers={"X-API-Key": "dev-key-123"})

    assert resp.status_code == 200
    assert isinstance(resp.json()["credits"], int)
    assert resp.json()["credits"] == 4
