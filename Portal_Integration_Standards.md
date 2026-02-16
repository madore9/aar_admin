# Portal Integration Standards

## 1) Repo Overview

### `myharvard-main` — Portal (Django SSR) + module host
- **Purpose:** Primary portal web app: routing, page shell, templates, role/permission wiring, and calls into the API service.
- **Tech stack:** Django 5.2.9 (Python 3.13), OIDC auth, Datadog tracing, Tailwind-generated CSS served as Django static, httpx client to API.
- **Key evidence:**
  - Django + Python version pin: `pyproject.toml` → `Django==5.2.9`, `requires-python = ">=3.13,<3.14"`.
  - Portal routes and module mounting: `app/myharvard/urls.py` (e.g. `path('student/', include("student_home.urls"))`).
  - OIDC backend: `app/myharvard/common/auth.py` (`Mozilla_django_oidc` backend; uses `preferred_username`).
  - Portal shell template: `app/portal/templates/layout.html` (includes `main.css`, `portal.css`, Preline, etc.)
  - API integration header: `app/myharvard/common/myharvard_api.py` (`myharvard_api_headers = {'X-API-KEY': ...}`).

---

### `myharvard-ui-main` — Design system + UI prototypes + built assets
- **Purpose:** Source for portal UI standards: component classes (`btn`, `form-control`, validation feedback), tokens, prototypes, and compiled CSS/JS assets.
- **Tech stack:** Tailwind CSS v4, Preline, Gulp pipeline.
- **Key evidence:**
  - Tailwind v4 + Preline: `package.json` (`"tailwindcss": "^4.0.6"`, `"preline": "^3.0.0"`).
  - Core component classes: `dist/assets/css/_core.source.min.css` (buttons, validation, etc.).
  - Token definitions: `dist/assets/css/_core.source.css` (e.g. `--color-primary`, `--radius-*`, typography scale).
  - Form patterns: `src/form-validation.html` (grid layout, required fields, `invalid-feedback` markup).
  - Prototype patterns (alerts/toasts/banners): `src/toasts.html`, `src/banners.html`, etc.

---

### `myharvardapi-main` — FastAPI service (data + SIS/portal APIs)
- **Purpose:** Backend API service (FastAPI) used by the portal; enforces API-key auth + scoped permissions; provides health/version endpoints; uses Redis cache; Oracle pools.
- **Tech stack:** FastAPI 0.120.0 (Python 3.13), fastapi-cache2 (Redis), oracledb, ddtrace, uvicorn.
- **Key evidence:**
  - App entry + middleware + system endpoints: `app/main.py` (`/healthCheck`, `/version`, middleware).
  - API-key auth + permission scopes: `app/utils/security.py` (hash + permission matching).
  - API key header name: `app/configs/config.py` (`APIKeyHeader(name="X-API-Key")`).
  - Router structure + prefixing: `app/routers/sis.py` (`BASE_URL = "/sis"` + `include_router(...)`).
  - Cache init and key builder: `app/main.py` + `app/configs/config.py`.

---

## 2) Standards Catalog (table)

> **Legend:**  
> **Evidence** = repo file path(s) you can open to verify.  
> **Example Snippet** = short excerpt copied from the repo (or lightly trimmed with `...`).

| Standard-ID | Category | Must/Should/Can | Standard Statement | Rationale | Evidence (file paths) | Example Snippet (short) |
|---|---|---|---|---|---|---|
| UI-001 | UI/UX | **Must** | New portal pages **must** use the shared portal shell (`layout.html`) and render within its content block. | Ensures consistent header/nav/footer, scripts, and theme behavior. | `myharvard-main/app/portal/templates/layout.html` | `{% extends "layout.html" %}` (expected in new templates) and `<!-- Main Content --> ... {% block content %}{% endblock %}` |
| UI-002 | UI/UX | **Must** | Pages **must** include portal CSS via the shell (do not ship page-specific CSS unless approved). | Prevents divergent styling and token drift. | `myharvard-main/app/portal/templates/layout.html` | `<link rel="stylesheet" href="{% static 'css/main.css' %}">` and `<link rel="stylesheet" href="{% static 'css/portal.css' %}">` |
| UI-003 | UI/UX | **Must** | Use design-system button classes for all buttons/CTAs (`btn`, `btn-primary`, `btn-white`, etc.). | Consistent sizing, spacing, hover/focus, dark-mode. | `myharvard-ui-main/dist/assets/css/_core.source.min.css`, `myharvard-ui-main/src/*.html` | `.btn { @apply px-3 md:px-4 ... h-10 md:h-12 ... rounded-lg ... }` and `.btn-primary { @apply ... bg-primary ... }` |
| UI-004 | UI/UX | **Must** | Use design-system icon button classes (`btn-icon`, `btn-icon-sm`, etc.) for icon-only actions. | Ensures hit target size + consistent affordances. | `myharvard-ui-main/dist/assets/css/_core.source.min.css`, `myharvard-main/app/portal/templates/alerts.html` | `.btn-icon { @apply ... size-10 md:size-12 rounded-full ... }` and `class="btn-icon btn-icon-sm btn-ghost"` |
| UI-005 | UI/UX | **Must** | Form fields **must** use `form-control` and labels use `form-label`. | Consistent typography/spacing; validation styling hooks. | `myharvard-ui-main/src/form-validation.html` | `<label class="form-label" ...>` and `<input ... class="form-control" required>` |
| UI-006 | UI/UX | **Must** | Client/server validation **must** follow the repo pattern: `required` + `invalid-feedback` elements; server errors mark inputs with `is-invalid` (or wrapper `.is-invalid`). | Standardizes inline error UX and error icon placement. | `myharvard-ui-main/src/form-validation.html`, `myharvard-ui-main/dist/assets/css/_core.source.min.css` | `class="form-control is-invalid"` and `<div class="invalid-feedback invalid-feedback-text">...` |
| UI-007 | UI/UX | **Must** | Validation styling **must** rely on `was-validated :invalid` and `.is-invalid` rules (don’t invent alternate error classnames). | Prevents one-off “error” styles that won’t match tokens/dark mode. | `myharvard-ui-main/dist/assets/css/_core.source.min.css` | `.was-validated :invalid, ... .is-invalid ... { @apply border-danger; }` |
| UI-008 | UI/UX | **Must** | Alerts/banners **must** include `role="alert"` and use `sr-only` for non-visible accessible labels (e.g., dismiss). | Baseline accessibility compliance + consistent alert UX. | `myharvard-main/app/portal/templates/alerts.html` | `<div ... role="alert">` and `<span class="sr-only">Dismiss</span>` |
| UI-009 | UI/UX | **Should** | Use the shared alert template pattern with severity mapping to tokens (warning/danger/success/primary). | Keeps semantic severity consistent across portal. | `myharvard-main/app/portal/templates/alerts.html` | `severity == 2 ... class="... bg-danger-light text-danger ..."` |
| UI-010 | UI/UX | **Must** | Use token-driven colors (`primary`, `danger`, `success`, etc.) rather than hard-coded hex values in templates. | Dark-mode + theming compatibility. | `myharvard-ui-main/dist/assets/css/main.min.css`, `myharvard-main/app/portal/static/css/main.css` | `--color-primary:#a51c30; ... --color-danger:#b91c1c; ...` |
| UI-011 | UI/UX | **Must** | Responsive layout **must** use Tailwind breakpoints and the portal’s grid conventions (12-col grid + `md:` variants). | Consistent responsive behavior across modules. | `myharvard-ui-main/src/form-validation.html` | `class="grid grid-cols-12 ... col-span-12 md:col-span-4 ..."` |
| UI-012 | UI/UX | **Should** | Prefer rounded radius tokens (`rounded-lg`, `rounded-2xl`) already used by components (avoid custom border-radius). | Visual consistency; tokenized radii. | `myharvard-ui-main/dist/assets/css/_skeleton.source.css` | `.skeleton-block { @apply rounded-lg md:rounded-2xl ... }` |
| UI-013 | UI/UX | **Can** | Use “compact view” utility variants for dense list views where applicable. | Provides an established density mode without bespoke CSS. | `myharvard-ui-main/dist/assets/css/_portal.source.css` | `.compact-view .compact-view\:p-6 { @apply p-6; } ... @media (width >= theme(--breakpoint-md)) { ... }` |
| FE-001 | Frontend Eng | **Must** | Do not introduce a new component framework for standard UI primitives; use the existing CSS class-based design system. | Portal is class-driven; prevents parallel component systems. | `myharvard-ui-main/src/*.html`, `myharvard-main/app/portal/static/css/main.css` | Repeated usage of `btn`, `form-control`, `form-label`, etc. across prototypes and shipped CSS. |
| FE-002 | Frontend Eng | **Must** | JS UI behaviors should use Preline hooks (`hs-*` attributes/classes) when available rather than custom JS widgets. | Aligns with existing script bundle + behaviors. | `myharvard-main/app/portal/templates/layout.html`, `myharvard-ui-main/package.json` | Layout loads Preline: `<script src="{% static 'js/preline.js' %}"></script>` and UI uses `data-hs-*` patterns (e.g. form select). |
| FE-003 | Frontend Eng | **Should** | Use the existing select pattern with `data-hs-select` templates and `form-control-select-*` classes. | Consistent select UX + keyboard behavior via shared library. | `myharvard-ui-main/src/form-validation.html` | `<select ... data-hs-select='{ "toggleClasses": "form-control-select ...", "dropdownClasses": "form-control-select-dropdown", ... }' ...>` |
| BE-001 | Django/Python | **Must** | Django projects integrated into the portal **must** run on Python 3.13 and pin dependencies via `uv.lock`. | Reproducible builds; matches portal runtime. | `myharvard-main/pyproject.toml`, `myharvard-main/uv.lock` | `requires-python = ">=3.13,<3.14"` and presence of `uv.lock` |
| BE-002 | Django/Python | **Must** | Environment selection **must** use `DJANGO_ENV` with module-per-env settings (`settings_local`, `settings_dev`, etc.). | Consistent configuration injection pattern. | `myharvard-main/app/myharvard/common/myharvard_api.py`, `myharvard-main/app/myharvard/settings_*.py` | `environment = os.getenv('DJANGO_ENV', 'local')` then `import_module(f".settings_{environment}", ...)` |
| BE-003 | Django/Python | **Must** | Authentication **must** use OIDC backend that maps users via `preferred_username`. | Aligns identity to HUID/username used throughout portal. | `myharvard-main/app/myharvard/common/auth.py` | `username = claims.get("preferred_username")` |
| BE-004 | Django/Python | **Must** | Authorization **must** use Django permissions as global “roles” via the `RolePerms` content-type model. | Ensures role checks work in views/templates and supports dynamic role sync. | `myharvard-main/app/portal/models/models.py`, `myharvard-main/app/myharvard/common/auth.py` | `managed = False ... default_permissions = ()` and comment: “use the Django permission model as global roles.” |
| BE-005 | Django/Python | **Must** | Role membership **must** be sourced from the API role endpoint and applied to Django permissions for the logged-in user. | Centralizes role truth; avoids duplicated role stores. | `myharvard-main/app/myharvard/common/auth.py`, `myharvard-main/app/myharvard/common/myharvard_api.py` | `roles = lookup_user_roles(user.username)` and `url_path = "/sis/roles/" + huid` |
| BE-006 | Django/Python | **Should** | Support delegated admin “hijack” only via the established permission gate (`portal.HU_PORTAL_PROXY`). | Prevents privilege escalation and ad-hoc impersonation. | `myharvard-main/app/myharvard/common/auth.py` | `return hijacker.has_perm('portal.HU_PORTAL_PROXY') and not hijacked.is_superuser` |
| API-001 | FastAPI | **Must** | FastAPI services **must** enforce API-key auth using header `X-API-Key`. | Portal already sends this header; consistent auth for service-to-service calls. | `myharvardapi-main/app/configs/config.py`, `myharvard-main/app/myharvard/common/myharvard_api.py` | `APIKeyHeader(name="X-API-Key")` and `myharvard_api_headers = {'X-API-KEY': ...}` *(HTTP headers are case-insensitive)* |
| API-002 | FastAPI | **Must** | Endpoints **must** declare required permission scopes and validate them via `Security(get_authenticated_user, scopes=[...])`. | Standardizes authorization + self-documenting permission needs. | `myharvardapi-main/app/routers/cs/course_search.py`, `myharvardapi-main/app/utils/security.py` | `user=Security(get_authenticated_user, scopes=[KeyPermissions.READ_COURSE_INFO])` |
| API-003 | FastAPI | **Must** | Permissions **must** be matched using wildcard-capable comparison against key permissions. | Enables coarse-to-fine permission grants without code changes. | `myharvardapi-main/app/utils/security.py` | `fnmatch.fnmatch(required, perm)` |
| API-004 | FastAPI | **Must** | Keys **must** be stored/compared hashed with a per-env SALT. | Avoids plaintext key material handling. | `myharvardapi-main/app/utils/security.py` | `salted_key = key + config_module.SALT` then `sha256(...)` |
| API-005 | FastAPI | **Must** | Routers **must** be composed under stable prefixes (e.g. `/sis`) using `include_router` composition. | Keeps routing consistent and avoids path sprawl. | `myharvardapi-main/app/routers/sis.py` | `BASE_URL = "/sis"` then `router = APIRouter(prefix=BASE_URL)` |
| API-006 | FastAPI | **Must** | Services **must** expose `/healthCheck` and `/version`. | Required for platform health gating and ops visibility. | `myharvardapi-main/app/main.py` | `@app.get("/version"... )` and `@app.get("/healthCheck"... )` |
| X-001 | Infra/Runtime | **Must** | Container images **must** run as a non-root user. | Baseline container hardening. | `myharvard-main/Dockerfile`, `myharvardapi-main/Dockerfile` | `useradd ... user` and `USER user` |
| X-002 | Infra/Runtime | **Must** | Dependency install **must** use `uv sync --no-dev --frozen` in container builds. | Reproducible, locked dependency resolution. | `myharvard-main/Dockerfile`, `myharvardapi-main/Dockerfile` | `RUN /bin/uv sync --no-dev --frozen` |
| X-003 | Observability | **Should** | Suppress noisy healthcheck access logs (or equivalent) to reduce log volume. | Keeps logs actionable and cost-contained. | `myharvardapi-main/app/main.py` | `HealthCheckFilter ... return '/healthCheck' not in record.getMessage()` |
| X-004 | Observability | **Can** | Use a cache key builder that normalizes query params for stable caching keys. | Reduces accidental cache misses. | `myharvardapi-main/app/configs/config.py` | `key_parts.append(repr(sorted(request.query_params.items())))` |
| INT-001 | Integration | **Must** | Portal-to-API calls **must** include `X-API-Key` and use base URL from settings (`MYHARVARD_API_URL`). | Ensures calls work in each environment without code changes. | `myharvard-main/app/myharvard/common/myharvard_api.py`, `myharvard-main/app/myharvard/settings_*.py` | `myharvard_api_url = settings.MYHARVARD_API_URL` and `headers={'X-API-KEY': ...}` |
| INT-002 | Integration | **Should** | New portal modules should mount routes via `app/myharvard/urls.py` under a clear prefix (e.g. `student/`, `activity-guide/`). | Keeps navigation + reverse routing predictable. | `myharvard-main/app/myharvard/urls.py` | `path('student/', include("student_home.urls"))` |
| CI-001 | CI/CD | **Should (Inferred)** | CI should fail if lockfiles drift from declared deps (uv). | Prevents “works on my machine” dependency drift. | **Inferred from** `uv.lock` usage and Docker build using `--frozen`. | `RUN /bin/uv sync --no-dev --frozen` (container build will fail if lock mismatched) |
| CI-002 | CI/CD | **Can** | Apply Datadog static analysis rulesets for Python. | Additional security + best practice gating. | `myharvardapi-main/static-analysis.datadog.yml` | `rulesets: - python-best-practices ... - python-security` |

**Unknown / not found in repos (so not standardized here):**
- A shared ESLint/Prettier config, Python lint config (ruff/flake8/black), test harness requirements, GitHub Actions workflows, OpenAPI error envelope conventions, structured logging schema, tracing correlation ID propagation, k8s readiness/liveness specs.

---

## 3) Golden Path Templates

### A) “New App Skeleton” (portal-integrated Django module)

```
my-new-module/
  app/
    my_new_module/
      __init__.py
      apps.py
      urls.py
      views/
        __init__.py
        views.py
      templates/
        my_new_module/
          index.html          # extends portal layout.html
          partials/...
      static/                # only if truly needed; prefer portal static bundles
      tests/                 # if you add tests (not standardized in repos)
  README.md
```

**Key config expectations (copy the portal’s patterns):**
- **Template base:** `myharvard-main/app/portal/templates/layout.html`
- **Role checks:** use Django permissions tied to `portal.RolePerms` (`myharvard-main/app/portal/models/models.py`)
- **Mounting:** add to `myharvard-main/app/myharvard/urls.py` under a stable prefix (e.g. `path('my-new-module/', include("my_new_module.urls"))`)

**Template starter (`index.html`):**
```django
{% extends "layout.html" %}
{% block content %}
  <div class="max-w-[96rem] mx-auto px-4">
    <!-- page content -->
  </div>
{% endblock %}
```
*(The `max-w-[96rem]` container pattern is used by portal alerts container: `app/portal/templates/alerts.html`.)*

---

### B) “New API Endpoint Checklist” (FastAPI)

1) **Router placement**
- Put endpoint in an existing router module or new module under `myharvardapi-main/app/routers/...`.
- Ensure it is reachable by composition via a parent router (e.g. `/sis`) (`app/routers/sis.py`).

2) **AuthZ**
- Require API key + scope:
  - `user=Security(get_authenticated_user, scopes=[KeyPermissions.<...>])` (`app/routers/cs/course_search.py`)
- If new permission is needed, add to your permissions enum location (see `app/routers/admin/admin.py` usage; not fully enumerated here).

3) **Caching (optional)**
- If safe/appropriate, add `@cache(expire=...)` (`app/routers/cs/course_search.py`)
- Ensure cache key stability is acceptable (`app/configs/config.py` request key builder)

4) **Errors**
- Raise `HTTPException(status_code=..., detail=...)` (common pattern in routers)
- **Unknown:** a standardized error envelope isn’t defined; don’t invent one without a portal-wide decision.

5) **Docs**
- Add `tags=[...]`, `response_model=...`, and meaningful `description=` (see `course_search.py`).

---

### C) “New UI Page Checklist” (portal page)

**Layout + assets**
- [ ] Template extends `layout.html` (`myharvard-main/app/portal/templates/layout.html`)
- [ ] Uses portal CSS (already included via shell): `main.css`, `portal.css`
- [ ] Uses container/grid conventions (`grid grid-cols-12`, `md:` responsive splits) (`myharvard-ui-main/src/form-validation.html`)

**Components**
- [ ] Buttons use `btn` variants (`btn-primary`, `btn-white`, etc.) (`myharvard-ui-main/dist/assets/css/_core.source.min.css`)
- [ ] Icon actions use `btn-icon` variants (`myharvard-ui-main/dist/assets/css/_core.source.min.css`)
- [ ] Forms use `form-label` + `form-control` (`myharvard-ui-main/src/form-validation.html`)

**Validation + a11y**
- [ ] Required fields use `required` attribute (`src/form-validation.html`)
- [ ] Inline errors use `invalid-feedback` + `invalid-feedback-text`/`icon` pattern (`src/form-validation.html`)
- [ ] Alerts use `role="alert"` and dismiss has `sr-only` label (`myharvard-main/app/portal/templates/alerts.html`)

---

## 4) Integration Contract

### Portal ⇄ API (service-to-service)
**Required request headers**
- **`X-API-Key`** (required)
  - API expects header name `X-API-Key` (`myharvardapi-main/app/configs/config.py`)
  - Portal sends `X-API-KEY` (`myharvard-main/app/myharvard/common/myharvard_api.py`)
  - **Note:** Header names are case-insensitive; do not “fix” casing unless you standardize it across repos.

**Base URL configuration**
- Portal uses `MYHARVARD_API_URL` from env-specific settings (`myharvard-main/app/myharvard/common/myharvard_api.py`).
- API selects env via `MYHARVARDAPI_ENV` and loads `app.configs.config_<env>` (`myharvardapi-main/app/configs/config.py`).

**Auth assumptions**
- API authorizes by:
  1) hashing `X-API-Key` with `config_module.SALT` (`myharvardapi-main/app/utils/security.py`)
  2) loading permissions for keys from DB table `API_PERMISSIONS` (`app/utils/security.py`)
  3) enforcing required endpoint scopes via `SecurityScopes` (`app/utils/security.py`, routers)

**Routing conventions**
- SIS endpoints live under `/sis` (`myharvardapi-main/app/routers/sis.py`).
- Portal calls role endpoint `/sis/roles/{huid}` (`myharvard-main/app/myharvard/common/myharvard_api.py`).

**Error handling**
- API uses `HTTPException` for endpoint-level failures; has global handler for `oracledb.Error` that maps to 500 (`myharvardapi-main/app/main.py`).
- **Unknown:** no shared JSON error envelope standard is defined in these repos.

**Observability requirements**
- API suppresses `/healthCheck` access log noise (`myharvardapi-main/app/main.py`).
- **Unknown:** correlation-id propagation or structured log schema is not standardized in these repos.

---

### Portal module integration (new apps inside portal)
**Mounting**
- New modules are mounted in `app/myharvard/urls.py` under a stable prefix (examples: `student/`, `activity-guide/`) (`myharvard-main/app/myharvard/urls.py`).

**AuthN**
- Portal uses OIDC via `mozilla_django_oidc` and maps to `preferred_username` (`myharvard-main/app/myharvard/common/auth.py`).

**AuthZ**
- Portal treats Django permissions as “roles” using the non-managed `RolePerms` model (`myharvard-main/app/portal/models/models.py`).
- Roles are refreshed from API role endpoint and mapped to Django `Permission` objects (`myharvard-main/app/myharvard/common/auth.py`).

---

## 5) Portal Compliance Rubric (one-page)

### Scoring + outcomes
- **MUST checks:** all must pass for **PASS** or **PASS WITH WARNINGS**.
- **SHOULD checks:** may fail and still pass, but trigger warnings.
- **Outcome rules:**
  - **PASS:** all MUST pass; ≤ 3 SHOULD fail
  - **PASS WITH WARNINGS:** all MUST pass; > 3 SHOULD fail
  - **NEEDS FIXES:** any MUST fails

---

### Top checks (mapped to Must/Should)

| # | Check | Level | How to validate | Common failure mode | Minimal remediation |
|---:|---|---|---|---|---|
| 1 | Templates extend portal shell | MUST | Open template: verify `{% extends "layout.html" %}` | Page renders without header/nav/scripts | Update template inheritance |
| 2 | Uses portal CSS bundles | MUST | Confirm shell includes `css/main.css` + `css/portal.css` | Team adds ad-hoc CSS overriding tokens | Remove custom CSS; use classes |
| 3 | Buttons use `btn` variants | MUST | Search for `<button ... class="btn ...">` | Raw Tailwind combos diverge from design | Replace with `.btn`, `.btn-primary`, etc. |
| 4 | Icon-only actions use `btn-icon` | MUST | Look for `.btn-icon` on icon buttons | Tiny hit targets / inconsistent hover | Use `.btn-icon` + size variant |
| 5 | Forms use `form-label` + `form-control` | MUST | Check markup in forms | Inputs look off; validation styling breaks | Apply standard classes |
| 6 | Validation uses `is-invalid` / `invalid-feedback` | MUST | Inspect invalid states | Custom “error” classes don’t trigger styling | Use `.is-invalid` + `.invalid-feedback-*` |
| 7 | Required fields use `required` attribute | MUST | Inspect HTML attributes | Users submit empty fields silently | Add `required` + feedback element |
| 8 | Alerts use `role="alert"` | MUST | Inspect alert markup | Screen readers don’t announce alerts | Add `role="alert"` |
| 9 | Dismiss controls have accessible label | MUST | Look for `sr-only` label (e.g. “Dismiss”) | Icon-only dismiss has no label | Add `<span class="sr-only">...` |
| 10 | Portal module mounted under stable prefix | SHOULD | Check `app/myharvard/urls.py` | Routes scattered at root | Add `path('my-module/', include(...))` |
| 11 | Uses OIDC identity mapping to `preferred_username` | MUST | If auth code touched: confirm in backend | Uses email/subject instead; breaks role lookup | Follow `MyHarvardOIDCBackend` pattern |
| 12 | Role checks use Django permissions (“roles”) | MUST | Confirm use of `user.has_perm(...)` patterns | Team adds separate role table | Use `RolePerms` + perms sync |
| 13 | Portal-to-API calls include `X-API-Key` | MUST | Confirm header in API client | 401 from API | Add header sourcing env var |
| 14 | API endpoints require scopes via `Security(...scopes=)` | MUST (API) | Open endpoint code | “Open” endpoints unintentionally exposed | Add `Security(get_authenticated_user, scopes=[...])` |
| 15 | API router included under `/sis` or appropriate prefix | MUST (API) | Check `routers/sis.py` composition | Endpoint unreachable; docs inconsistent | `include_router` under stable prefix |
| 16 | `/healthCheck` exists and works | MUST | Run service; `GET /healthCheck` | No health endpoint → ops can’t gate deploys | Add endpoint as in `app/main.py` |
| 17 | `/version` returns version | MUST | `GET /version` | Can’t identify running build | Implement env-or-file version read |
| 18 | Containers run non-root | MUST | Inspect Dockerfile (`USER user`) | Root container flagged by security | Add non-root user + `USER` |
| 19 | Container build uses `uv ... --frozen` | MUST | Inspect Dockerfile | Lock drift; unreproducible builds | Use `uv.lock` + `--frozen` |
| 20 | Preline patterns used for interactive UI (where applicable) | SHOULD | Look for `data-hs-*` usage | Custom JS reinvents widgets | Adopt Preline hooks |

---

### “PR gate” version (what reviewers should block on)
**Block merge if any of these are failing:**
- Checks **1–9, 11–9** (all MUST rows above)
- API merges: **14–19** also become blocking when adding/changing API

---

### Required CI checks (must be green to merge)

**Repo-evidenced (treat these as REQUIRED because builds rely on them):**
1) **Docker build succeeds**
- Evidence: both repos ship Dockerfiles (`myharvard-main/Dockerfile`, `myharvardapi-main/Dockerfile`)
2) **Locked dependency install succeeds (`uv ... --frozen`)**
- Evidence: Docker build runs `uv sync --no-dev --frozen` in both Dockerfiles

**Should add (Inferred; not present as workflows in repos):**
- Django: `python manage.py check` and `python manage.py collectstatic --noinput`
  - Evidence that collectstatic is part of build: `myharvard-main/Dockerfile` runs `manage.py collectstatic`
- API: lightweight smoke: `GET /healthCheck` (service starts)
  - Evidence health endpoint exists: `myharvardapi-main/app/main.py`

---

### PR template snippet (teams should use)

```md
## Portal Integration Checklist

### Must
- [ ] Templates extend `layout.html` and render inside `{% block content %}`
- [ ] Buttons/forms use design-system classes (`btn*`, `form-control`, `form-label`)
- [ ] Validation uses `is-invalid` + `invalid-feedback` pattern
- [ ] Alerts/dismiss controls meet accessibility basics (`role="alert"`, `sr-only`)
- [ ] If calling portal API: sends `X-API-Key` and uses env-configured base URL
- [ ] If adding API endpoints: uses `Security(get_authenticated_user, scopes=[...])`
- [ ] `/healthCheck` and `/version` available (API services)
- [ ] Docker build passes and uses `uv ... --frozen`
- [ ] Container runs non-root (`USER user`)

### Should
- [ ] Routes mounted under a stable prefix in `app/myharvard/urls.py`
- [ ] Uses Preline patterns (`data-hs-*`) for interactive widgets where applicable

### Evidence
- Link to screenshots (UI) / curl outputs (API) / relevant file paths:
```

---

## 6) Anti-drift Controls

### Version pinning (Must)
- **Pin Python runtime to 3.13** (already enforced by both pyprojects)
  - Evidence: `myharvard-main/pyproject.toml` and `myharvardapi-main/pyproject.toml` both require `>=3.13,<3.14`.
- **Use `uv.lock` and frozen installs**
  - Evidence: `uv.lock` exists, and Docker builds run `uv sync --no-dev --frozen` in both repos.

**How to validate**
- In CI: run the container build; it will fail if lock drift exists.
- Locally: run `uv sync --frozen` (same failure mode as Docker).

### Shared UI asset drift control (Should)
- Treat `myharvard-ui-main/dist/assets/css/*` as the source of truth for component classes and tokens.
- Portal static CSS currently contains Tailwind output (e.g. `myharvard-main/app/portal/static/css/main.css` begins with Tailwind banner and token definitions), implying it is built/copied from the UI pipeline.

**How to validate**
- Diff token sections (`--color-primary`, `--radius-*`, etc.) between:
  - `myharvard-ui-main/dist/assets/css/main.min.css` (or `_core.source.css`)
  - `myharvard-main/app/portal/static/css/main.css`

### Static analysis (Can)
- API repo provides Datadog static analysis ruleset config.
  - Evidence: `myharvardapi-main/static-analysis.datadog.yml`

**How to validate**
- Run your org’s Datadog static analysis job using that ruleset file.

---

## 7) Open Questions / Gaps

These are **not derivable** from the repos as provided; marking as **Unknown** and listing where I expected to find evidence:

1) **CI workflow definition (Unknown)**
- Expected: `.github/workflows/*.yml` in each repo (none found).
- Needed decision: exact required checks, test commands, artifact publishing.

2) **Python lint/format standards (Unknown)**
- Expected: `ruff.toml`, `.flake8`, `pyproject` tool sections, `pre-commit-config.yaml` (not found).
- Needed decision: ruff/black/isort/mypy? plus enforcement level.

3) **Frontend lint/format standards (Unknown)**
- Expected: `.eslintrc`, `prettier` config (not found).

4) **API error envelope + pagination + versioning policy (Unknown)**
- Expected: shared `schemas/errors.py` or middleware implementing an error response model (not found).
- Current observed pattern: endpoints raise `HTTPException(... detail=str(e))` (`myharvardapi-main/app/routers/cs/course_search.py`).

5) **Correlation IDs / distributed tracing propagation (Unknown)**
- Expected: middleware adding/requesting `X-Request-Id` or similar; structured log formatter; tracing config (not found).
- Observed: ddtrace dependency exists in both Python projects (`pyproject.toml`), but no clear propagation standard in code shown.

6) **Secrets management + config injection policy (Unknown)**
- Expected: deployment manifests, parameter-store references, or config docs (not found).  
- Observed: env vars used (`DJANGO_ENV`, `MYHARVARDAPI_ENV`, API key envs), but no formal policy.
