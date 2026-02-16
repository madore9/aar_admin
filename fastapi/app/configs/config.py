import os
from importlib import import_module

aar_env = os.getenv("AAR_ENV", "local")
config_module = import_module(f"app.configs.config_{aar_env}")

# Re-export all config values
DATABASE_PATH = getattr(config_module, "DATABASE_PATH", "aar_admin.db")
API_KEY = getattr(config_module, "API_KEY", "dev-key-123")
