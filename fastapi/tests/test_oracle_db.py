"""
Unit tests for app.databases.oracle_db

Tests the oracle_query helper and pool lifecycle in isolation.
No real Oracle connection is required — the pool is mocked.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import app.databases.oracle_db as oracle_db_module
from app.databases.oracle_db import oracle_query, init_oracle_pool, close_oracle_pool


# ---------------------------------------------------------------------------
# oracle_query — pool unavailable
# ---------------------------------------------------------------------------

async def test_oracle_query_returns_empty_when_pool_is_none(monkeypatch):
    """When _pool is None, oracle_query must return [] immediately."""
    monkeypatch.setattr(oracle_db_module, "_pool", None)
    result = await oracle_query("SELECT 1 FROM DUAL")
    assert result == []


# ---------------------------------------------------------------------------
# oracle_query — pool available, happy path
# ---------------------------------------------------------------------------

async def test_oracle_query_returns_rows_when_pool_available(monkeypatch):
    """When _pool is set and cursor returns data, we get a list of dicts."""
    # Build mock cursor
    mock_cursor = AsyncMock()
    mock_cursor.description = [("SYSTEM_ID",), ("ID",), ("TITLE",), ("DEPARTMENT",), ("CREDITS",)]
    mock_cursor.fetchall = AsyncMock(return_value=[
        ("001234", "CS 50", "Intro to CS", "CS", 4),
    ])

    # Wrap in async context manager
    mock_cursor_cm = AsyncMock()
    mock_cursor_cm.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor_cm.__aexit__ = AsyncMock(return_value=False)

    mock_conn = AsyncMock()
    mock_conn.cursor = MagicMock(return_value=mock_cursor_cm)

    mock_conn_cm = AsyncMock()
    mock_conn_cm.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn_cm.__aexit__ = AsyncMock(return_value=False)

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=mock_conn_cm)

    monkeypatch.setattr(oracle_db_module, "_pool", mock_pool)

    result = await oracle_query("SELECT * FROM PS_CRSE_CAT_R3_VW WHERE INSTITUTION = :inst", {"inst": "HRVRD"})

    assert len(result) == 1
    assert result[0]["system_id"] == "001234"
    assert result[0]["id"] == "CS 50"
    assert result[0]["credits"] == 4


async def test_oracle_query_lowercases_column_names(monkeypatch):
    """Column names from cursor.description must be lowercased."""
    mock_cursor = AsyncMock()
    mock_cursor.description = [("SYSTEM_ID",), ("COURSE_TITLE_LONG",)]
    mock_cursor.fetchall = AsyncMock(return_value=[("001234", "Intro to CS")])

    mock_cursor_cm = AsyncMock()
    mock_cursor_cm.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor_cm.__aexit__ = AsyncMock(return_value=False)

    mock_conn = AsyncMock()
    mock_conn.cursor = MagicMock(return_value=mock_cursor_cm)

    mock_conn_cm = AsyncMock()
    mock_conn_cm.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn_cm.__aexit__ = AsyncMock(return_value=False)

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=mock_conn_cm)

    monkeypatch.setattr(oracle_db_module, "_pool", mock_pool)
    result = await oracle_query("SELECT SYSTEM_ID, COURSE_TITLE_LONG FROM DUAL")

    assert "system_id" in result[0]
    assert "course_title_long" in result[0]
    # Original uppercase keys must NOT be present
    assert "SYSTEM_ID" not in result[0]


# ---------------------------------------------------------------------------
# oracle_query — exception handling
# ---------------------------------------------------------------------------

async def test_oracle_query_returns_empty_on_db_exception(monkeypatch):
    """Any exception from Oracle must be caught and return []."""
    mock_cursor = AsyncMock()
    mock_cursor.execute = AsyncMock(side_effect=Exception("ORA-00942: table not found"))

    mock_cursor_cm = AsyncMock()
    mock_cursor_cm.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor_cm.__aexit__ = AsyncMock(return_value=False)

    mock_conn = AsyncMock()
    mock_conn.cursor = MagicMock(return_value=mock_cursor_cm)

    mock_conn_cm = AsyncMock()
    mock_conn_cm.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn_cm.__aexit__ = AsyncMock(return_value=False)

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=mock_conn_cm)

    monkeypatch.setattr(oracle_db_module, "_pool", mock_pool)
    result = await oracle_query("SELECT * FROM NONEXISTENT_TABLE")

    assert result == []


# ---------------------------------------------------------------------------
# init_oracle_pool — DSN empty
# ---------------------------------------------------------------------------

async def test_init_pool_skips_when_dsn_empty(monkeypatch):
    """When ORACLE_DSN is empty, _pool stays None and no oracledb call is made."""
    monkeypatch.setattr(oracle_db_module, "_pool", None)
    monkeypatch.setattr("app.databases.oracle_db.ORACLE_DSN", "")

    with patch("app.databases.oracle_db.ORACLE_DSN", ""):
        await init_oracle_pool()

    assert oracle_db_module._pool is None


async def test_init_pool_sets_pool_when_dsn_provided(monkeypatch):
    """When DSN is set, create_pool_async is called and _pool is set."""
    monkeypatch.setattr(oracle_db_module, "_pool", None)

    fake_pool = MagicMock()
    with patch("app.databases.oracle_db.ORACLE_DSN", "host:1521/svc"), \
         patch("app.databases.oracle_db.ORACLE_USER", "testuser"), \
         patch("app.databases.oracle_db.ORACLE_PASSWORD", "testpass"):

        with patch("oracledb.create_pool_async", new_callable=AsyncMock, return_value=fake_pool):
            await init_oracle_pool()

    assert oracle_db_module._pool is fake_pool


# ---------------------------------------------------------------------------
# close_oracle_pool
# ---------------------------------------------------------------------------

async def test_close_pool_when_pool_is_none(monkeypatch):
    """close_oracle_pool must not raise when pool is already None."""
    monkeypatch.setattr(oracle_db_module, "_pool", None)
    await close_oracle_pool()  # should not raise
    assert oracle_db_module._pool is None


async def test_close_pool_calls_pool_close(monkeypatch):
    """close_oracle_pool must call pool.close() and set _pool back to None."""
    fake_pool = AsyncMock()
    fake_pool.close = AsyncMock()
    monkeypatch.setattr(oracle_db_module, "_pool", fake_pool)

    await close_oracle_pool()

    fake_pool.close.assert_awaited_once()
    assert oracle_db_module._pool is None
