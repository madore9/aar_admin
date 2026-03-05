import logging
import logging.config
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from app.databases import sqlite_db
from app.databases.oracle_db import init_oracle_pool, close_oracle_pool
from app.services.seed_data import seed_database
from app.routers import aar
from app.configs.config import REDIS_URL

# Load logging configuration
logging.config.fileConfig(
    os.path.join(os.path.dirname(__file__), "logging.conf"),
    disable_existing_loggers=False,
)
logger = logging.getLogger(__name__)


class HealthCheckLogFilter(logging.Filter):
    """Suppress /healthCheck request noise from access logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "/healthCheck" in msg:
            return False
        return True


# Apply filter to uvicorn access logger so /healthCheck doesn't flood logs
logging.getLogger("uvicorn.access").addFilter(HealthCheckLogFilter())


@asynccontextmanager
async def lifespan(app: FastAPI):
    aar_env = os.environ.get("AAR_ENV", "local")
    logger.info(f"AAR Admin API starting, env={aar_env}")
    await sqlite_db.init_db()
    await seed_database()
    await init_oracle_pool()   # no-ops silently when ORACLE_DSN is empty

    # --- Cache backend -------------------------------------------------------
    # Local dev: in-memory cache (no Redis server required)
    # All other envs: Redis backend (AAR_REDIS_URL env var sets the URL)
    _redis_client = None
    if aar_env == "local":
        FastAPICache.init(InMemoryBackend(), prefix="aar")
        logger.info("Cache: InMemoryBackend (local dev, no Redis required)")
    else:
        import redis.asyncio as aioredis
        from fastapi_cache.backends.redis import RedisBackend
        _redis_client = aioredis.from_url(REDIS_URL)
        FastAPICache.init(RedisBackend(_redis_client), prefix="aar")
        logger.info(f"Cache: RedisBackend at {REDIS_URL}")

    logger.info("AAR Admin API ready")
    yield

    logger.info("AAR Admin API shutting down")
    if _redis_client:
        await _redis_client.aclose()
    await close_oracle_pool()
    await sqlite_db.close_db()


app = FastAPI(title="AAR Admin API", version="0.1.0", lifespan=lifespan)
app.include_router(aar.router)


@app.get("/healthCheck")
async def health_check():
    healthy = await sqlite_db.check_health()
    return {"status": "OK" if healthy else "ERROR"}


@app.get("/version")
async def version():
    return {"version": "0.1.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions, log them, and return a clean 500."""
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
