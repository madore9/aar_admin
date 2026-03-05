"""
API key authentication for AAR Admin API.
Mirrors myharvardapi/utils/security.py pattern.
"""
import hashlib
import logging
from enum import Enum

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader, SecurityScopes

from app.configs.config import config_module

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class KeyPermissions(str, Enum):
    READ_PLANS = "read:plans"
    WRITE_PLANS = "write:plans"
    READ_COURSES = "read:courses"
    READ_COURSE_LISTS = "read:course_lists"
    WRITE_COURSE_LISTS = "write:course_lists"
    READ_AUDIT = "read:audit"
    WRITE_AUDIT = "write:audit"


def hash_api_key(key: str) -> str:
    salt = getattr(config_module, 'SALT', 'aar-admin-dev-salt')
    return hashlib.sha256(f"{key}{salt}".encode()).hexdigest()


async def get_authenticated_user(
    required_permissions: SecurityScopes,
    api_key: str | None = Security(api_key_header),
):
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")

    # For local dev, accept the dev key directly
    valid_key = getattr(config_module, 'API_KEY', 'dev-key-123')
    if api_key != valid_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # In local dev, all permissions granted
    return {"api_key": api_key, "permissions": [p.value for p in KeyPermissions]}
