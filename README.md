# EC2 Co-Tenancy Deployment Package

This package lets you deploy your Docker app alongside the existing MCP server on EC2, using path-based routing (e.g., `/admin/`, `/myapp/`).

## Quick Start

1. **Choose your app name and URL path:**
   - App name: alphanumeric, starts with letter (e.g., `admin-panel`, `django-app`)
   - URL path: starts with `/` (e.g., `/admin`, `/portal`, `/myapp`)

2. **Run the deployment script:**
   ```bash
   ./deploy_secondary.sh <app-name> <url-path> [port]
   
   # Example for Django admin at /admin/
   ./deploy_secondary.sh admin-panel /admin 8000
   ```

3. **Follow the output instructions** to add nginx and docker-compose config

## Files Included

| File | Purpose |
|------|---------|
| `deploy_secondary.sh` | Generates config snippets (manual, safer) |
| `deploy_secondary_full.sh` | Auto-updates configs (faster) |
| `Dockerfile` | Reference Django Dockerfile |
| `requirements.txt` | Django dependencies |
| `myapp/` | Reference Django project structure |
| `gunicorn.conf.py` | Production Gunicorn config |

## What You Need to Prepare

### 1. Your Docker Image
- Must have a `Dockerfile` in your project root
- Must expose a port (default: 8000)
- Must have a `/health/` endpoint returning `{"status": "ok"}`
- Should use non-root user
- Should include HEALTHCHECK instruction

### 2. Environment Variables
Add these to your app:
- `APP_NAME` - your app's name
- `APP_PATH` - URL prefix (e.g., `/admin`)
- `APP_PORT` - internal port (e.g., `8000`)
- `DJANGO_SECRET_KEY` - your secret key
- `DATABASE_URL` - if using a database

### 3. Django-Specific Settings
If using Django:
```python
# settings.py
ALLOWED_HOSTS = ['*']  # or the EC2 IP
FORCE_SCRIPT_NAME = '/admin'  # your URL prefix
STATIC_URL = '/admin/static/'
DEBUG = False
```

## Deployment Flow

```
Your Machine                    EC2
     │                           │
     │  1. Copy app code         │
     ├──────────────────────────►│
     │                           │
     │  2. Build container       │
     │  ───────────────────────► │
     │                           │
     │  3. nginx routes /admin/ │
     │  ───────────────────────► │
     │                           │
     │  4. App accessible at     │
     │     https://<host>/admin/ │
```

## Safe Commands (won't break MCP)

| Safe | Dangerous |
|------|-----------|
| `docker compose build myapp` | `docker compose down` |
| `docker compose up -d myapp` | `docker compose up -d` |
| `docker compose restart myapp` | `docker compose restart` |
| `docker compose logs myapp` | `docker compose logs` (no service) |

## Need Help?

- Full guide: `../thoughts/django_cotenancy_guide_v1.md`
- EC2 host: `10.138.149.157`
- SSH key: `myharvard-dev-mcp.pem`

## Testing Locally

To test your Docker container before deploying to EC2:

```bash
# Build
docker build -t myadmin .

# Run
docker run -p 8000:8000 -e APP_NAME=admin -e APP_PATH=/admin myadmin

# Test health
curl http://localhost:8000/health/

# Test from outside container
curl http://localhost:8000/admin/
```
