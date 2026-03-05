# EC2 Co-Tenancy Deployment Guide

This guide explains how to deploy your Docker app alongside the existing MCP server on the shared EC2 instance using path-based routing.

---

## Purpose

We have a single EC2 instance with one IP/domain, running the PeopleSoft MCP server at `/peoplesoft/`. We need to deploy additional applications (like this Django admin app) to the same server without:

- **Impacting the MCP server** - It must stay running at all times
- **Getting a new IP/domain** - We only have one available
- **Creating a separate portal** - Single entry point for all services

The solution is **path-based routing** via nginx: different URL paths route to different Docker containers, all on the same port 443.

---

## Architecture

```
Client → nginx (:443) → /peoplesoft/* → peoplesoft-mcp:8080 (existing MCP)
                   → /your-app/*     → your-app:8000 (your new app)
```

Your app gets its own URL path (e.g., `/admin/`, `/aar/`, `/portal/`) without affecting the MCP server.

---

## Quick Start

### Step 1: Choose Your App Details

| Item | Example | Notes |
|------|---------|-------|
| App name | `aar-admin` | Alphanumeric, starts with letter |
| URL path | `/aar/` | Starts with `/`, ends with `/` |
| Port | `8000` | Internal container port |

### Step 2: Generate Deployment Configs

Run the deployment script:

```bash
cd /Users/crm990/AI/aar_admin
./deploy_secondary.sh <app-name> <url-path> [port]

# Example
./deploy_secondary.sh aar-admin /aar 8000
```

This outputs:
- nginx configuration snippet
- docker-compose.yml service snippet
- Commands to run on EC2

### Step 3: Add Configs to MCP Server

Copy the generated snippets to the MCP server at `~/peoplesoft_mcp/`:

1. **nginx.conf** - Add the upstream + location block inside the `server` block
2. **docker-compose.yml** - Add the service under `services:`

### Step 4: Deploy

```bash
# SSH to EC2
ssh -i myharvard-dev-mcp.pem ec2-user@10.138.149.157

# Reload nginx (non-disruptive)
sudo docker exec nginx-prod nginx -s reload

# Build and start your app
cd ~/peoplesoft_mcp
sudo docker compose build aar-admin
sudo docker compose up -d aar-admin
```

Your app will be at: `https://<host>/aar/`

---

## Django App Requirements

Your Django app must meet these requirements:

### 1. Health Endpoint

```python
# urls.py
from django.http import JsonResponse

def health(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path('health/', health),
    # ...
]
```

### 2. Settings for EC2

```python
# settings.py
import os

APP_NAME = os.environ.get('APP_NAME', 'aar-admin')
APP_PATH = os.environ.get('APP_PATH', '/aar/')
APP_PORT = os.environ.get('APP_PORT', '8000')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-me')

DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

ALLOWED_HOSTS = ['*']  # or the EC2 IP

# Force script name for URL generation behind nginx
FORCE_SCRIPT_NAME = APP_PATH

# Static files
STATIC_URL = f'{APP_PATH}static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

### 3. Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -ms /bin/bash app && mkdir /app && chown -R app /app
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=app . .

# Collect static files
RUN python manage.py collectstatic --noinput || true

USER app
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

# Gunicorn
CMD ["gunicorn", "myapp.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
```

### 4. Production WSGI Server

Use Gunicorn, not `manage.py runserver`:

```bash
# requirements.txt
gunicorn>=21.0
```

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 2
timeout = 120
```

---

## Safe Commands

These commands target only your app (won't affect MCP):

| Safe | Dangerous |
|------|-----------|
| `docker compose build aar-admin` | `docker compose down` |
| `docker compose up -d aar-admin` | `docker compose up -d` |
| `docker compose restart aar-admin` | `docker compose restart` |
| `docker compose logs aar-admin` | `docker compose logs` (no service) |

---

## Environment Variables

Add these to your app's environment:

| Variable | Example | Description |
|----------|---------|-------------|
| `APP_NAME` | `aar-admin` | Your app name |
| `APP_PATH` | `/aar/` | URL prefix |
| `APP_PORT` | `8000` | Internal port |
| `DJANGO_SECRET_KEY` | `xyz...` | Django secret |
| `DATABASE_URL` | `postgres://...` | Database connection |

---

## Troubleshooting

### Static files 404
- Set `STATIC_URL = '/aar/static/'`
- Run `collectstatic` in Dockerfile

### CSRF errors
- Add `CSRF_TRUSTED_ORIGINS = ['http://10.138.149.157']` to settings

### URL generation wrong
- Set `FORCE_SCRIPT_NAME = '/aar/'` so Django generates correct URLs

### Database connection fails
- Ensure credentials are in environment variables
- Database must be accessible from EC2

---

## EC2 Details

| Item | Value |
|------|-------|
| Host | `10.138.149.157` |
| SSH Key | `myharvard-dev-mcp.pem` |
| MCP Server Path | `~/peoplesoft_mcp/` |
| Your App Path | `~/aar-admin/` |

---

## Files Reference

| File | Purpose |
|------|---------|
| `deploy_secondary.sh` | Generates config snippets |
| `deploy_secondary_full.sh` | Auto-updates configs |
| `Dockerfile` | Template for your app |
| `gunicorn.conf.py` | Production server config |
| `requirements.txt` | Python dependencies |

---

## Future Updates

When updating your app:

```bash
# On EC2
cd ~/aar-admin
git pull origin main

# Rebuild and restart ONLY your app
cd ~/peoplesoft_mcp
sudo docker compose build aar-admin
sudo docker compose up -d aar-admin
```

No nginx reload needed unless you change the URL path.
