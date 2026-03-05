"""
Cache utilities for AAR Admin API.

Provides a key builder that excludes the `user` dependency-injection parameter
from cache keys so caching is based on request data only — not which API key
made the request.  Without this, every unique auth context would generate its
own cache entry for identical data, defeating the cache entirely.
"""
import hashlib

from fastapi_cache import FastAPICache


def aar_key_builder(
    func,
    namespace: str = "",
    request=None,
    response=None,
    args: tuple = (),
    kwargs: dict | None = None,
) -> str:
    """Cache key from function name + request params, auth stripped out."""
    kw = dict(kwargs or {})
    kw.pop("user", None)  # auth is a separate concern from data identity
    prefix = FastAPICache.get_prefix()
    raw = f"{prefix}:{namespace}:{func.__module__}:{func.__name__}:{args}:{kw}"
    return hashlib.md5(raw.encode()).hexdigest()
