# my.harvard Portal — Infrastructure Checklist for New Apps

> **Purpose:** Verify that a new Python app follows the same architectural patterns as the my.harvard portal. Use this checklist during development, code review, and pre-deployment to ensure consistency across all co-tenant applications.
>
> **Reference Implementation:** AAR Admin (`/aar-admin/`)
> **Last Updated:** 2026-02-26

---

## Quick Reference: The Stack

| Layer | Technology | Role |
|-------|-----------|------|
| Frontend | Django 5.x + Jinja2 templates | UI rendering, user sessions, OIDC auth |
| Design System | TailwindCSS 4 + Preline + HTMX | Styling, components, interactivity |
| API | FastAPI 0.120+ | Business logic, data access, caching |
| Cache | Redis (prod) / InMemory (dev) | Response caching, session storage |
| Local Storage | SQLite via aiosqlite | Audit logs, drafts, local preferences |
| Source of Truth | PeopleSoft Oracle via python-oracledb | Academic data (read-only) |
| Package Manager | uv | Dependency management + lockfiles |
| Deployment | Docker co-tenant on shared EC2 | Path-based routing behind nginx |

---

## 1. PROJECT STRUCTURE

### [ ] Directory Layout

```
your-app/
├── docker-compose.yml            # Multi-service orchestration
├── .gitignore                    # Must include .env, __pycache__, db.sqlite3
├── README.md                     # Co-tenancy safety rules
│
├── django/                       # Frontend layer
│   ├── Dockerfile
│   ├── pyproject.toml            # uv-managed deps
│   ├── uv.lock
│   ├── start-server.sh           # Entry point for Docker
│   └── app/
│       ├── manage.py
│       ├── <project_name>/       # Django project config package
│       │   ├── settings.py       # Base settings (all envs)
│       │   ├── settings_local.py # Local dev overrides
│       │   ├── settings_dev.py   # EC2 dev deployment
│       │   ├── settings_prod.py  # Production deployment
│       │   ├── urls.py           # Root URL dispatcher
│       │   ├── asgi.py
│       │   ├── wsgi.py
│       │   ├── context_processors.py
│       │   └── common/
│       │       └── <app>_api.py  # FastAPI HTTP client (centralized)
│       └── <app>/                # Django app(s)
│           ├── views/
│           ├── services/         # Business logic layer
│           └── templates/
│
├── fastapi/                      # API layer
│   ├── Dockerfile
│   ├── pyproject.toml            # uv-managed deps + pytest config
│   ├── uv.lock
│   ├── start-server.sh
│   ├── .env                      # Gitignored — Oracle credentials
│   ├── <app_name>.db             # SQLite database file
│   └── app/
│       ├── main.py               # Entry point + lifespan
│       ├── logging.conf
│       ├── cache.py              # Cache key builder
│       ├── configs/
│       │   ├── config.py         # Dynamic env-based loader
│       │   └── config_local.py   # Local dev config (loads .env)
│       ├── routers/
│       │   ├── <base>.py         # Composed router with shared prefix
│       │   ├── <resource>.py     # Resource-specific endpoints
│       │   └── ...
│       ├── databases/
│       │   ├── sqlite_db.py      # SQLite connection + query helpers
│       │   └── oracle_db.py      # Oracle pool + fallback
│       ├── schemas/              # Pydantic models
│       │   └── <resource>.py
│       ├── services/
│       │   └── seed_data.py      # Idempotent seed data
│       └── utils/
│           └── security.py       # API key auth + permissions
│
└── tests/                        # Test suite (inside fastapi/)
    ├── conftest.py               # Shared fixtures
    ├── test_<resource>.py        # Integration tests per resource
    └── validate_oracle.py        # Manual Oracle validation script
```

### Checklist

- [ ] Django and FastAPI are in **separate directories** with their own `Dockerfile` and `pyproject.toml`
- [ ] Each layer has its own `start-server.sh` entry point
- [ ] No shared Python packages between Django and FastAPI (communicate only via HTTP)
- [ ] Tests live inside `fastapi/tests/` (FastAPI owns all data tests)
- [ ] `.env` file is in `fastapi/` root and is gitignored

---

## 2. DJANGO FRONTEND LAYER

### [ ] Settings Architecture

| File | Purpose | Key Settings |
|------|---------|-------------|
| `settings.py` | Base (all envs) | `INSTALLED_APPS`, `MIDDLEWARE`, `TEMPLATES`, `DATABASES` |
| `settings_local.py` | Local dev | `DEBUG=True`, `ALLOWED_HOSTS=['*']`, `LocMemCache` |
| `settings_dev.py` | EC2 dev | `DEBUG=False`, `FORCE_SCRIPT_NAME`, Redis cache |
| `settings_prod.py` | Production | `DEBUG=False`, secure cookies, Redis+TLS, ManifestStorage |

**Checklist:**

- [ ] `FORCE_SCRIPT_NAME = '/<app-path>'` is set in `settings_dev.py` and `settings_prod.py`
- [ ] `STATIC_URL` includes the app path prefix (e.g., `/<app-path>/static/`)
- [ ] `CSRF_TRUSTED_ORIGINS` includes the correct domain for each environment
- [ ] `SESSION_COOKIE_SECURE = True` and `CSRF_COOKIE_SECURE = True` in production
- [ ] `SECRET_KEY` is loaded from environment in production (never hardcoded)
- [ ] `ALLOWED_HOSTS` is loaded from environment (comma-separated) in dev/prod
- [ ] Cache backend: `LocMemCache` for local, `RedisCache` for dev/prod
- [ ] Settings module selection via `DJANGO_SETTINGS_MODULE` env var

### [ ] API Client (Django → FastAPI)

The Django layer **never accesses databases directly**. All data flows through the FastAPI API via an HTTP client.

```python
# common/<app>_api.py — centralized API client
import httpx
from django.conf import settings

AAR_API_URL = settings.AAR_API_BASE_URL   # e.g., "http://localhost:9223"
API_KEY = settings.AAR_API_KEY            # e.g., "dev-key-123"
TIMEOUT = 10.0

async def api_get(path: str, params: dict = None) -> dict:
    """GET request to FastAPI. Path is relative (e.g., '/courses/')."""
    url = f"{AAR_API_URL}/aar{path}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers={"X-API-Key": API_KEY}, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

async def api_post(path: str, data: dict) -> dict: ...
async def api_put(path: str, data: dict) -> dict: ...
async def api_delete(path: str) -> dict: ...
```

**Checklist:**

- [ ] Single centralized API client module (not scattered httpx calls)
- [ ] Base URL and API key loaded from Django settings
- [ ] All requests include `X-API-Key` header
- [ ] Timeout is set (10s default)
- [ ] Async `httpx.AsyncClient` used (matches async Django views)
- [ ] Path construction: `f"{BASE_URL}/aar{path}"` (consistent prefix)
- [ ] Error handling: `raise_for_status()` or equivalent

### [ ] Views Pattern

- [ ] All views are **async** (`async def view_name(request):`)
- [ ] Views call service layer functions, not the API client directly
- [ ] Service layer calls the API client and returns structured data
- [ ] Templates receive pre-processed data from views (no API calls in templates)

### [ ] Templates and Design System

- [ ] Jinja2 template engine (not Django's default)
- [ ] Base template extends the my.harvard design system layout
- [ ] TailwindCSS 4 loaded via CDN (or compiled locally)
- [ ] Preline UI components for dropdowns, modals, tabs
- [ ] HTMX for dynamic page updates without full reload
- [ ] Context processors inject common data (navigation, user info)

---

## 3. FASTAPI API LAYER

### [ ] Main Application (`main.py`)

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    await sqlite_db.init_db()        # Create tables
    await seed_database()            # Idempotent seed data
    await init_oracle_pool()         # No-ops if ORACLE_DSN empty
    # Cache backend (conditional)
    if aar_env == "local":
        FastAPICache.init(InMemoryBackend(), prefix="<app>")
    else:
        FastAPICache.init(RedisBackend(redis_client), prefix="<app>")

    yield  # App is running

    # --- Shutdown ---
    await close_oracle_pool()
    await sqlite_db.close_db()

app = FastAPI(title="<App> API", version="0.1.0", lifespan=lifespan)
```

**Checklist:**

- [ ] Lifespan uses `@asynccontextmanager` (not deprecated `@app.on_event`)
- [ ] Startup order: SQLite init → seed data → Oracle pool → cache
- [ ] Shutdown order: Oracle close → SQLite close
- [ ] Cache backend: `InMemoryBackend` for local, `RedisBackend` for prod
- [ ] Health check endpoint at `/healthCheck` (excluded from access logs)
- [ ] Global exception handler returns clean 500s (no stack traces to clients)
- [ ] Health check log filter suppresses `/healthCheck` noise

### [ ] Configuration Management

```python
# config.py — dynamic env-based import
aar_env = os.getenv("AAR_ENV", "local")
config_module = import_module(f"app.configs.config_{aar_env}")

# Re-export with safe defaults
DATABASE_PATH   = getattr(config_module, "DATABASE_PATH", "<app>.db")
API_KEY         = getattr(config_module, "API_KEY", "dev-key-123")
ORACLE_DSN      = getattr(config_module, "ORACLE_DSN", "")
ORACLE_USER     = getattr(config_module, "ORACLE_USER", "")
ORACLE_PASSWORD = getattr(config_module, "ORACLE_PASSWORD", "")
```

```python
# config_local.py — local dev with .env support
from dotenv import load_dotenv
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_file)

DATABASE_PATH = str(Path(__file__).resolve().parent.parent.parent / "<app>.db")
ORACLE_DSN      = os.environ.get("ORACLE_DSN", "")
ORACLE_USER     = os.environ.get("ORACLE_USER", "")
ORACLE_PASSWORD = os.environ.get("ORACLE_PASSWORD", "")
```

**Checklist:**

- [ ] Config selected dynamically via `AAR_ENV` env var (default: `local`)
- [ ] `config_local.py` loads `.env` file via `python-dotenv`
- [ ] All paths use `Path(__file__).resolve()` (not relative paths)
- [ ] Oracle credentials default to empty string (triggers SQLite fallback)
- [ ] `getattr()` with safe defaults in `config.py` (survives missing attrs)
- [ ] `.env` file exists at `fastapi/.env` and is in `.gitignore`

### [ ] Router Organization

```python
# routers/<base>.py — composed router
BASE_URL = "/aar"  # or "/your-app-prefix"
router = APIRouter(prefix=BASE_URL)
router.include_router(resource1.router)
router.include_router(resource2.router)
```

```python
# routers/<resource>.py — resource-specific
router = APIRouter(prefix="/courses", tags=["courses"])

@router.get("/", response_model=CourseSearchResponse)
@cache(expire=600, namespace="courses", key_builder=aar_key_builder)
async def search_courses(
    q: str = Query(None),
    user=Security(get_authenticated_user, scopes=[KeyPermissions.READ_COURSES]),
): ...
```

**Checklist:**

- [ ] Base router with app-wide prefix (`/aar`, `/your-app`)
- [ ] Sub-routers with resource-specific prefixes (`/courses`, `/plans`)
- [ ] Every endpoint has `Security()` dependency for auth
- [ ] Every GET endpoint has `@cache()` decorator with appropriate TTL
- [ ] Response models declared on every endpoint (`response_model=...`)
- [ ] Tags for Swagger UI grouping

### [ ] Security (API Key Auth)

```python
# utils/security.py
class KeyPermissions(str, Enum):
    READ_COURSES = "read:courses"
    WRITE_PLANS  = "write:plans"
    # ... scope per resource + operation

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_authenticated_user(
    required_permissions: SecurityScopes,
    api_key: str | None = Security(api_key_header),
):
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
    if api_key != valid_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return {"api_key": api_key, "permissions": [...]}
```

**Checklist:**

- [ ] API key passed via `X-API-Key` header (not query param)
- [ ] `KeyPermissions` enum defines granular scopes (`read:resource`, `write:resource`)
- [ ] `Security()` dependency injection on every endpoint
- [ ] 401 returned for missing/invalid key (not 403)
- [ ] Local dev grants all permissions to the dev key
- [ ] API key hashed with salt for storage comparison

### [ ] Pydantic Schemas

```python
class Course(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    system_id: str
    title: str
    department: str
    credits: int
```

**Checklist:**

- [ ] All models use `ConfigDict(from_attributes=True, extra="ignore")`
- [ ] `from_attributes=True` — allows construction from SQLite Row dicts
- [ ] `extra="ignore"` — silently drops unknown DB columns
- [ ] Field names match SQLite column names AND Oracle SQL aliases
- [ ] Enums for constrained string fields (plan types, scopes, etc.)
- [ ] Separate Request vs Response models where needed

### [ ] Caching

```python
# cache.py
def aar_key_builder(func, namespace="", request=None, response=None, args=(), kwargs=None):
    kw = dict(kwargs or {})
    kw.pop("user", None)  # Auth is not part of cache identity
    raw = f"{prefix}:{namespace}:{func.__module__}:{func.__name__}:{args}:{kw}"
    return hashlib.md5(raw.encode()).hexdigest()
```

**Checklist:**

- [ ] Custom key builder strips auth dependency from cache key
- [ ] Key includes namespace, module, function name, and query params
- [ ] MD5 hash for compact Redis keys
- [ ] `InMemoryBackend` for local dev (no Redis dependency)
- [ ] `RedisBackend` for dev/prod
- [ ] Cache cleared after write operations: `await FastAPICache.clear(namespace="...")`
- [ ] TTLs: 5-10 min for lists, 15-30 min for detail views

---

## 4. DATABASE LAYER

### [ ] SQLite (Local Storage)

```python
# databases/sqlite_db.py
_db = None  # Module-level singleton

async def get_db():
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DATABASE_PATH)
        _db.row_factory = aiosqlite.Row
    return _db

async def execute_query(sql, params=None, fetch_one=False):
    """SELECT with retry logic (3 attempts, 1s delay)."""
    ...

async def execute_write(sql, params=None):
    """INSERT/UPDATE/DELETE with auto-commit and retry."""
    ...
```

**Checklist:**

- [ ] Async via `aiosqlite`
- [ ] `row_factory = aiosqlite.Row` (dict-like access)
- [ ] Singleton connection pattern (module-level `_db`)
- [ ] Retry logic on both read and write (3 attempts, 1s delay)
- [ ] `execute_query` returns `list[dict]` or single `dict` with `fetch_one=True`
- [ ] `execute_write` auto-commits and returns `lastrowid`
- [ ] `CREATE TABLE IF NOT EXISTS` for all tables in `init_db()`
- [ ] Tables created on startup (idempotent)

### [ ] Oracle (PeopleSoft Source of Truth)

```python
# databases/oracle_db.py
_pool = None  # None = Oracle unavailable

async def init_oracle_pool():
    """No-ops silently when ORACLE_DSN is empty."""
    if not ORACLE_DSN:
        logger.info("Oracle DSN not configured — SQLite fallback active")
        return
    _pool = oracledb.create_pool_async(
        user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN,
        min=1, max=5, increment=1,
    )

async def oracle_query(sql, params=None) -> list[dict]:
    """Returns [] on any failure — never raises."""
    if _pool is None:
        return []
    # ... execute and return list of dicts
```

**Checklist:**

- [ ] `python-oracledb` in thin mode (no Oracle Instant Client)
- [ ] `create_pool_async()` is **not** awaited (returns pool directly)
- [ ] `pool.close()` **is** awaited (drains connections)
- [ ] Pool min=1, max=5, increment=1 (conservative for co-tenancy)
- [ ] `_pool = None` is the signal for "Oracle unavailable"
- [ ] `oracle_query()` returns `[]` on any error (never raises)
- [ ] Column names lowercased from `cursor.description`
- [ ] Named bind variables: `:param_name` with dict params
- [ ] Init no-ops silently when `ORACLE_DSN` is empty string
- [ ] All Oracle access is **read-only** (SELECT only, no INSERT/UPDATE/DELETE)

### [ ] Dual-Path Fallback Pattern

```python
async def _oracle_search(q, field) -> Optional[list[dict]]:
    """Returns:
    - list[dict]  → Oracle responded (may be empty)
    - None        → Oracle unavailable, use SQLite
    """
    if oracle_db._pool is None:
        return None     # Signal: use SQLite
    rows = await oracle_query(primary_sql, params)
    if rows:
        return rows
    rows = await oracle_query(fallback_sql, params)
    return rows         # May be [] (genuinely no results)

@router.get("/")
async def search(q=Query(None), ...):
    ps_rows = await _oracle_search(q, field)
    if ps_rows is not None:
        return Response(data=[coerce(r) for r in ps_rows])
    # SQLite fallback
    data = await execute_query(sqlite_sql, params)
    return Response(data=data)
```

**Checklist:**

- [ ] `None` return = Oracle unavailable (fall back to SQLite)
- [ ] `[]` return = Oracle responded with zero results (do NOT fall back)
- [ ] Primary query uses PS-delivered view (e.g., `PS_CRSE_CAT_R3_VW`)
- [ ] Fallback query uses manual JOIN (same data, different access path)
- [ ] `_coerce_row()` normalizes Oracle types (Decimal → int, whitespace trimming)
- [ ] `INSTITUTION = 'HRVRD'` filter on all PS queries (Harvard-specific)
- [ ] PeopleSoft effective-date pattern: `MAX(EFFDT) WHERE EFFDT <= SYSDATE AND EFF_STATUS = 'A'`
- [ ] `FETCH FIRST N ROWS ONLY` for result limiting (Oracle 12c+ syntax)

### [ ] Seed Data

```python
async def seed_database():
    rows = await execute_query("SELECT COUNT(*) as cnt FROM <primary_table>")
    if rows[0]["cnt"] > 0:
        return  # Already seeded — preserve existing data
    # ... insert seed data
```

**Checklist:**

- [ ] Idempotency guard: checks row count before seeding
- [ ] Called in FastAPI lifespan, after `init_db()`
- [ ] Never deletes existing data
- [ ] Single commit at end of seed operation
- [ ] Seed data defined as Python dicts in the same file

---

## 5. TESTING

### [ ] Test Infrastructure

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Checklist:**

- [ ] `asyncio_mode = "auto"` — no `@pytest.mark.asyncio` needed
- [ ] Tests in `fastapi/tests/` directory
- [ ] `conftest.py` with shared fixtures
- [ ] Dev dependencies: `pytest`, `pytest-asyncio`, `httpx`

### [ ] Required Fixtures

| Fixture | Purpose |
|---------|---------|
| `app_client` | `TestClient` with auth bypassed |
| `disable_cache` | Patches `@cache` to be a no-op (autouse) |
| `oracle_available` | Patches `_pool` to truthy + mocks `oracle_query` |
| `oracle_unavailable` | Sets `_pool = None` (SQLite fallback) |

**Checklist:**

- [ ] Auth bypassed via `app.dependency_overrides[get_authenticated_user]`
- [ ] Cache disabled globally with `autouse=True` fixture
- [ ] Oracle mock patches BOTH `oracle_db_module._pool` AND `app.routers.<resource>.oracle_query`
- [ ] `monkeypatch.setattr()` for module-level variables
- [ ] `patch()` context manager for import-time function references

### [ ] Required Test Cases

For each resource endpoint:

- [ ] **Oracle path**: Returns correct data when Oracle is available
- [ ] **Schema validation**: Response contains all required fields
- [ ] **Search/filter**: Query params produce correct subset
- [ ] **SQLite fallback**: Returns data when Oracle unavailable (no 500)
- [ ] **404 handling**: Returns 404 for missing resources (both paths)
- [ ] **Auth guard**: Returns 401/403 without API key
- [ ] **Type coercion**: Oracle Decimal/None values handled correctly

### [ ] Oracle Validation Script

```python
# tests/validate_oracle.py — manual, not pytest
# Run: python -m tests.validate_oracle
async def main():
    await init_oracle_pool()
    # 1. Pool initialized?
    # 2. View accessible? Row count?
    # 3. Sample search returns results?
    # 4. Keyword search works?
    # 5. Single record lookup?
    # 6. All schema fields present?
    # 7. Credits coerced to int?
```

**Checklist:**

- [ ] Standalone script (not discovered by pytest)
- [ ] Run with real Oracle credentials
- [ ] Checks: pool init, view access, search, lookup, schema fields, type coercion
- [ ] Reports pass/fail per check with clear output

---

## 6. DOCKER & DEPLOYMENT

### [ ] Docker Compose

```yaml
services:
  <app>-redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  <app>-api:
    build: ./fastapi
    ports: ["9223:9223"]
    volumes:
      - api-data:/app/data
    environment:
      - AAR_ENV=local
    depends_on:
      <app>-redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9223/healthCheck"]

  <app>-django:
    build: ./django
    ports: ["8000:8000"]
    environment:
      - DJANGO_SETTINGS_MODULE=<project>.settings_local
      - AAR_API_BASE_URL=http://<app>-api:9223
    depends_on:
      <app>-api:
        condition: service_healthy
```

**Checklist:**

- [ ] Three services: Redis, FastAPI, Django
- [ ] Health checks on Redis and FastAPI
- [ ] Django depends on FastAPI (service_healthy)
- [ ] FastAPI depends on Redis (service_healthy)
- [ ] Named volume for SQLite persistence (`api-data:/app/data`)
- [ ] Django `AAR_API_BASE_URL` points to FastAPI service name (not localhost)

### [ ] Dockerfile Pattern

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv sync --no-dev --frozen || pip install -e .
COPY . .
RUN chmod +x start-server.sh
EXPOSE <port>
CMD ["./start-server.sh"]
```

**Checklist:**

- [ ] Python 3.13-slim base image
- [ ] `uv` for dependency management
- [ ] `--no-dev --frozen` for production (no dev deps, use lockfile)
- [ ] Fallback to `pip install -e .` if uv fails
- [ ] Copy `pyproject.toml` before app code (layer caching)
- [ ] `start-server.sh` as entry point

### [ ] Co-Tenancy Safety

**CRITICAL: These rules prevent killing other apps on the shared EC2.**

- [ ] `docker compose build <service-name>` — always target by service
- [ ] **NEVER** bare `docker compose down` (kills all tenants)
- [ ] **NEVER** bare `docker compose restart` (restarts all services)
- [ ] No internet on EC2 — all deps baked into Docker image
- [ ] `FORCE_SCRIPT_NAME = '/<app-path>'` in Django dev/prod settings
- [ ] Nginx location block routes `/<app-path>/` to the correct upstream
- [ ] Static files served from `/<app-path>/static/`

### [ ] Port Allocation

| Service | Port | Notes |
|---------|------|-------|
| Django | 8000 | User-facing UI |
| FastAPI | 9223 | Internal API (not exposed to users) |
| Redis | 6379 | Cache + sessions |

*Coordinate port numbers with other tenants on the EC2 to avoid conflicts.*

---

## 7. AUTHENTICATION FLOW

### [ ] Full Auth Chain

```
User → Browser → nginx → Django (OIDC session)
                            ↓
                     Django adds X-API-Key header
                            ↓
                     FastAPI validates X-API-Key
                            ↓
                     FastAPI checks KeyPermissions scope
                            ↓
                     Response flows back up
```

**Checklist:**

- [ ] Django handles OIDC login via `mozilla-django-oidc`
- [ ] Django session stored in Redis (dev/prod)
- [ ] Django→FastAPI: API key in `X-API-Key` header (not user session)
- [ ] FastAPI validates API key against config
- [ ] FastAPI checks permission scopes per endpoint
- [ ] No user credentials pass through to FastAPI (API key only)
- [ ] Local dev: static API key (`dev-key-123`), all permissions granted

---

## 8. LOGGING & MONITORING

### [ ] Logging Configuration

```ini
# logging.conf
format=%(asctime)s loglevel=%(levelname)-6s logger=%(name)s %(funcName)s() L%(lineno)-4d %(message)s
```

**Checklist:**

- [ ] Python `logging.conf` file (not programmatic config)
- [ ] Root logger at INFO level
- [ ] Console handler outputs to stdout (Docker-friendly)
- [ ] Format includes: timestamp, level, logger name, function, line number
- [ ] Health check filter suppresses `/healthCheck` log noise
- [ ] All Oracle errors logged with `logger.error()` (not silently swallowed)
- [ ] Startup messages log environment, cache backend, Oracle status

---

## 9. ENVIRONMENT VARIABLES REFERENCE

### FastAPI

| Variable | Default | Purpose |
|----------|---------|---------|
| `AAR_ENV` | `local` | Config module selection (`config_local`, `config_dev`, `config_prod`) |
| `ORACLE_DSN` | `""` (empty) | Oracle connection string; empty = SQLite fallback |
| `ORACLE_USER` | `""` | Oracle username |
| `ORACLE_PASSWORD` | `""` | Oracle password |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |

### Django

| Variable | Default | Purpose |
|----------|---------|---------|
| `DJANGO_SETTINGS_MODULE` | `<project>.settings_local` | Settings module selection |
| `DJANGO_ENV` | `local` | Alternative env selector (used in wsgi.py) |
| `AAR_API_BASE_URL` | `http://localhost:9223` | FastAPI base URL |
| `AAR_API_KEY` | `dev-key-123` | API key for FastAPI calls |
| `DJANGO_SECRET_KEY` | (required in prod) | Django secret key |
| `ALLOWED_HOSTS` | `*` (local) | Comma-separated allowed hosts |
| `REDIS_URL` | `redis://localhost:6379` | Redis for cache + sessions |

### Credential Management

- [ ] `.env` file at `fastapi/.env` for Oracle credentials
- [ ] `load_dotenv()` in `config_local.py` (no-ops if file missing)
- [ ] Shell env vars (`~/.zshrc`) override `.env` values
- [ ] Single-quote passwords with special characters in shell (`$`, `#`, `!`)
- [ ] Never commit `.env` files (verified in `.gitignore`)

---

## 10. PRE-DEPLOYMENT CHECKLIST

### Before First Deploy

- [ ] All unit tests pass: `cd fastapi && python -m pytest tests/ -v`
- [ ] Oracle validation passes: `python -m tests.validate_oracle`
- [ ] FastAPI starts cleanly with correct log messages
- [ ] Django UI renders plans, requirements, and courses
- [ ] `FORCE_SCRIPT_NAME` is set correctly in dev/prod settings
- [ ] Static files collected: `python manage.py collectstatic`
- [ ] Docker images build successfully: `docker compose build`
- [ ] Docker services start and pass health checks
- [ ] nginx location block configured for `/<app-path>/`
- [ ] Port numbers don't conflict with other co-tenants

### Before Each Release

- [ ] All tests still pass
- [ ] No new `.env` files or credentials in git history
- [ ] Docker images rebuilt with latest dependencies
- [ ] Oracle connection tested against target environment
- [ ] Cache cleared if schema changes affect cached responses
- [ ] Audit log entries being created for write operations

---

## APPENDIX: Common Gotchas

| Gotcha | Solution |
|--------|----------|
| `'AsyncConnectionPool' object can't be awaited` | `create_pool_async()` is synchronous — don't `await` it |
| `pool.close()` hangs | `pool.close()` IS async — do `await` it |
| Password with `$#!` breaks in `.zshrc` | Use single quotes: `export VAR='value$#!'` |
| Oracle returns `Decimal` for numeric fields | Use `_coerce_row()` to convert: `int(row.get("credits") or 0)` |
| UGRD is not a valid Harvard career code | Harvard uses school-based codes: HCOL, FAS, GSAS, etc. |
| `PS_CRSE_CAT_R3_VW` has no ACAD_CAREER column | Filter by `INSTITUTION = 'HRVRD'` only, no career filter |
| Tests fail with "module not found" | Patch both `oracle_db_module.oracle_query` AND `app.routers.<resource>.oracle_query` |
| Django returns blank pages | FastAPI server is down — Django proxies all data through FastAPI |
| `docker compose down` kills everything | Always target by service name: `docker compose restart <service>` |
| `.env` values ignored when shell vars set | `load_dotenv()` never overrides existing env vars (by design) |
