import httpx
from django.conf import settings

AAR_API_URL = getattr(settings, 'AAR_API_BASE_URL', 'http://localhost:9223')


async def api_get(path: str, params: dict = None) -> dict | list | None:
    async with httpx.AsyncClient(base_url=AAR_API_URL, timeout=20.0) as client:
        response = await client.get(f"/aar{path}", params=params, follow_redirects=True)
        response.raise_for_status()
        if response.content:
            return response.json()
        return None


async def api_post(path: str, data: dict = None) -> dict | None:
    async with httpx.AsyncClient(base_url=AAR_API_URL, timeout=20.0) as client:
        response = await client.post(f"/aar{path}", json=data, follow_redirects=True)
        response.raise_for_status()
        if response.content:
            return response.json()
        return None


async def api_put(path: str, data: dict = None) -> dict | None:
    async with httpx.AsyncClient(base_url=AAR_API_URL, timeout=20.0) as client:
        response = await client.put(f"/aar{path}", json=data, follow_redirects=True)
        response.raise_for_status()
        if response.content:
            return response.json()
        return None


async def api_delete(path: str) -> bool:
    async with httpx.AsyncClient(base_url=AAR_API_URL, timeout=20.0) as client:
        response = await client.delete(f"/aar{path}", follow_redirects=True)
        return response.status_code < 400
