"""
Oracle database connection pool for reading PeopleSoft CS data.

Design decisions:
- Pool is None when ORACLE_DSN is not configured (local dev fallback).
- oracle_query() returns [] on any failure — callers treat [] as "use SQLite instead".
- Uses python-oracledb in thin mode (no Oracle Instant Client required).
- Named bind variables (:param) match Oracle/PeopleCode conventions.
"""
import logging

from app.configs.config import ORACLE_DSN, ORACLE_USER, ORACLE_PASSWORD

logger = logging.getLogger(__name__)

# Module-level pool; None until init_oracle_pool() succeeds.
_pool = None


async def init_oracle_pool() -> None:
    """Initialize the Oracle async connection pool.

    No-ops silently when ORACLE_DSN is empty (local dev with no Oracle access).
    Called from FastAPI lifespan on startup.
    """
    global _pool
    if not ORACLE_DSN:
        logger.info("Oracle DSN not configured — Oracle pool skipped (SQLite fallback active)")
        return
    try:
        import oracledb
        _pool = oracledb.create_pool_async(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN,
            min=1,
            max=5,
            increment=1,
        )
        logger.info(f"Oracle connection pool initialized: {ORACLE_DSN}")
    except Exception as e:
        logger.error(f"Oracle pool init failed: {e} — SQLite fallback active")
        _pool = None


async def oracle_query(sql: str, params: dict | None = None) -> list[dict]:
    """Execute a SELECT against Oracle and return a list of row dicts.

    Returns [] if the pool is unavailable (DSN not set, Oracle down, or init failed).
    Returns [] on any query error — callers treat an empty result as "fall back to SQLite".
    Bind variables use Oracle named style: :param_name with a dict.
    """
    if _pool is None:
        return []
    try:
        async with _pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params or {})
                # Build column names from cursor description (lowercase for Pydantic compat)
                cols = [d[0].lower() for d in cur.description]
                rows = await cur.fetchall()
                return [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        logger.error(f"Oracle query failed: {e}")
        return []


async def close_oracle_pool() -> None:
    """Close the Oracle pool on app shutdown."""
    global _pool
    if _pool is not None:
        try:
            await _pool.close()
            logger.info("Oracle connection pool closed")
        except Exception as e:
            logger.error(f"Oracle pool close error: {e}")
        finally:
            _pool = None
