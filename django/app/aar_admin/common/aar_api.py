"""
Centralized AAR API client.

Mirrors myharvard/common/myharvard_api.py — single module for all
FastAPI backend communication. All views import from here; no raw
httpx usage elsewhere in the Django codebase.
"""
import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

AAR_API_URL = getattr(settings, 'AAR_API_BASE_URL', 'http://localhost:9223')
AAR_API_KEY = getattr(settings, 'AAR_API_KEY', 'dev-key-123')

_api_headers = {
    'X-API-Key': AAR_API_KEY,
}


# ---------------------------------------------------------------------------
# Async API helpers (primary — used by async views)
# ---------------------------------------------------------------------------

async def aar_api_request(
    method: str,
    path: str,
    params: dict = None,
    json_data: dict = None,
    timeout: float = 20.0,
) -> dict | list | None:
    """
    Send an async request to the AAR FastAPI backend.

    Returns parsed JSON on success, None on any failure.
    Mirrors the my.harvard pattern: log the call, catch specific
    exceptions, return None so views can degrade gracefully.
    """
    url = f"{AAR_API_URL}/aar{path}"
    logger.info(f"AAR API {method.upper()} {url}")

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method,
                url,
                params=params,
                json=json_data,
                headers=_api_headers,
                follow_redirects=True,
            )
            response.raise_for_status()
            if response.content:
                return response.json()
            return None

    except httpx.HTTPStatusError as e:
        logger.error(f"AAR API HTTP error: {method.upper()} {url} -> {e.response.status_code} {e.response.text[:200]}")
    except httpx.TimeoutException:
        logger.error(f"AAR API timeout: {method.upper()} {url}")
    except httpx.RequestError as e:
        logger.error(f"AAR API request error: {method.upper()} {url} -> {e}")
    except Exception as e:
        logger.error(f"AAR API unexpected error: {method.upper()} {url} -> {e}")

    return None


# ---------------------------------------------------------------------------
# Convenience wrappers (match the old api_client.py signatures)
# ---------------------------------------------------------------------------

async def api_get(path: str, params: dict = None) -> dict | list | None:
    """GET request to AAR API."""
    return await aar_api_request("GET", path, params=params)


async def api_post(path: str, data: dict = None) -> dict | list | None:
    """POST request to AAR API."""
    return await aar_api_request("POST", path, json_data=data)


async def api_put(path: str, data: dict = None) -> dict | list | None:
    """PUT request to AAR API."""
    return await aar_api_request("PUT", path, json_data=data)


async def api_delete(path: str) -> bool:
    """DELETE request to AAR API. Returns True on success, False on error."""
    url = f"{AAR_API_URL}/aar{path}"
    logger.info(f"AAR API DELETE {url}")
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.delete(url, headers=_api_headers, follow_redirects=True)
            return response.status_code < 400
    except httpx.HTTPStatusError as e:
        logger.error(f"AAR API DELETE error: {url} -> {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"AAR API DELETE request error: {url} -> {e}")
    return False
