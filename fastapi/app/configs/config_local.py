import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the fastapi/ project root (one level above app/).
# No-ops silently if the file doesn't exist — safe for CI/production.
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_file)

# Anchored to this file's location — stable regardless of uvicorn launch CWD.
DATABASE_PATH = str(Path(__file__).resolve().parent.parent.parent / "aar_admin.db")
API_KEY = "dev-key-123"
SALT = "aar-admin-dev-salt"
REDIS_URL = "redis://localhost:6379"

# Oracle (PeopleSoft CS database).
# Leave empty for local dev — activates SQLite seed data fallback automatically.
# Set via environment variables when Oracle access is available.
ORACLE_DSN      = os.environ.get("ORACLE_DSN", "")       # e.g. "10.138.149.157:1521/c9pr2"
ORACLE_USER     = os.environ.get("ORACLE_USER", "")
ORACLE_PASSWORD = os.environ.get("ORACLE_PASSWORD", "")
