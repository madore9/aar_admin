from pathlib import Path

# Anchored to this file's location — stable regardless of uvicorn launch CWD.
DATABASE_PATH = str(Path(__file__).resolve().parent.parent.parent / "aar_admin.db")
API_KEY = "dev-key-123"
SALT = "aar-admin-dev-salt"
REDIS_URL = "redis://localhost:6379"
