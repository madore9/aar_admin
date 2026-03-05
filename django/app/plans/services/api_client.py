"""
API client shim — delegates to aar_admin.common.aar_api.

Kept for backward compatibility so existing imports in plan_service.py
continue to work. New code should import directly from aar_admin.common.aar_api.
"""
from aar_admin.common.aar_api import api_get, api_post, api_put, api_delete  # noqa: F401
