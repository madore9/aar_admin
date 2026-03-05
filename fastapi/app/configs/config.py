import os
from importlib import import_module

aar_env = os.getenv("AAR_ENV", "local")
config_module = import_module(f"app.configs.config_{aar_env}")

# Re-export all config values
DATABASE_PATH   = getattr(config_module, "DATABASE_PATH", "aar_admin.db")
API_KEY         = getattr(config_module, "API_KEY", "dev-key-123")
REDIS_URL       = getattr(config_module, "REDIS_URL", "redis://localhost:6379")

# Oracle — empty string means "no Oracle access; use SQLite fallback"
ORACLE_DSN      = getattr(config_module, "ORACLE_DSN", "")
ORACLE_USER     = getattr(config_module, "ORACLE_USER", "")
ORACLE_PASSWORD = getattr(config_module, "ORACLE_PASSWORD", "")
